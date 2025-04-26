import os
import json
import io
from openai import OpenAI
from model.dto import AnalyzeResponse
from typing import Dict, Optional
import pypdf
import docx
from utils.logger import logger
from utils.exception import DocanalyzerException
from utils.error_code import ErrorCode
from config import settings


DEFAULT_CRITERIA = {
    "Clarity": "Is the writing clear, concise, and easy to understand? Avoids jargon and ambiguity.",
    "Correctness": "Is the information presented accurate? Are grammar, spelling, and punctuation correct?",
    "Completeness": "Does the document cover the topic adequately? Are there any significant omissions?",
    "Structure": "Is the document well-organized with a logical flow? Are headings and paragraphs used effectively?",
    "Engagement": "Is the content engaging and interesting to the target audience (teachers/students)?"
}


class AnalyzerService:
    def __init__(self):
        # Initialize OpenAI client
        # The API key is automatically picked up from the OPENAI_API_KEY environment variable
        try:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
            # Test connection (optional, but good practice)
            self.openai_client.models.list()
            logger.info("OpenAI client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            # Depending on the application, you might want to raise the exception
            # or handle it in a way that the application can still run in a degraded mode.
            self.openai_client = None

    # --- Modify signature to accept filename ---
    async def analyze_document(self, file_content: bytes, filename: str, criteria: Optional[Dict[str, str]] = None) -> Optional[AnalyzeResponse]:
        logger.info(f"Starting analysis for file: {filename}")

        # 1. Parse the document content
        # --- Pass filename to parser ---
        parsed_content = await self._parse_document_content(file_content, filename)
        if parsed_content is None: # Check for None explicitly
            logger.error(f"Document parsing failed for {filename}. Aborting analysis.")
            # Use a more specific error? Consider adding ErrorCode.DOCUMENT_EMPTY_ERROR
            raise DocanalyzerException(*ErrorCode.DOCUMENT_PARSING_ERROR.value)
        elif not parsed_content.strip(): # Handle case where parsing succeeds but yields empty content
             logger.warning(f"Document parsing yielded empty content for {filename}. Proceeding with empty content.")
             # Option: raise DocanalyzerException(*ErrorCode.DOCUMENT_EMPTY_ERROR.value) # Create this error code if needed

        # Use default criteria if none provided
        final_criteria = criteria if criteria else DEFAULT_CRITERIA
        logger.info(f"Using criteria: {list(final_criteria.keys())}")

        # 2. Call LLM for feedback and scores
        analysis_result = self._call_llm_for_analysis(parsed_content, final_criteria)
        if not analysis_result:
            logger.error("LLM analysis failed. Aborting analysis.")
            raise DocanalyzerException(*ErrorCode.LLM_ANALYSIS_ERROR.value)

        # 3. Calculate overall score (optional)
        scores = analysis_result.get('scores', {})
        overall_score = None
        if scores:
            try:
                # Ensure scores are numeric (float or int)
                numeric_scores = {k: float(v) for k, v in scores.items()}
                overall_score = sum(numeric_scores.values()) / len(numeric_scores) if numeric_scores else 0
                logger.info(f"Calculated overall score: {overall_score:.2f}")
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not calculate overall score due to invalid score format: {e}. Scores: {scores}")
                overall_score = None  # Set to None if calculation fails

        # 4. Create response DTO
        response = AnalyzeResponse(
            feedback=analysis_result.get('feedback', 'Error: Feedback not generated.'),
            scores=scores,  # Keep original scores dict, even if some weren't numeric for overall calc
            overall_score=overall_score,
            # Optionally include parsed content for debugging/display
            # parsed_content=parsed_content
        )

        logger.info(f"Analysis complete for file: {filename}")
        return response

    # --- Modify signature and implementation ---
    async def _parse_document_content(self, file_content: bytes, filename: str) -> Optional[str]:
        """Parses the document content based on filename extension."""
        try:
            file_ext = os.path.splitext(filename)[1].lower()
            text_content = ""
            file_stream = io.BytesIO(file_content) # Use BytesIO for in-memory processing

            logger.info(f"Attempting to parse file '{filename}' with extension '{file_ext}'")

            if file_ext == ".pdf":
                # Use pypdf
                reader = pypdf.PdfReader(file_stream)
                num_pages = len(reader.pages)
                logger.info(f"Detected PDF with {num_pages} pages.")
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text: # Append only if text extraction was successful
                        text_content += page_text + "\\n"
            elif file_ext == ".docx":
                # Use python-docx
                document = docx.Document(file_stream)
                logger.info(f"Detected DOCX document.")
                for para in document.paragraphs:
                    text_content += para.text + "\\n"
            elif file_ext == ".md":
                # Use markdown library - needs decoding
                # Assuming UTF-8, adjust if other encodings are expected
                try:
                    markdown_text = file_content.decode('utf-8')
                    # Passing raw Markdown might be sufficient for the LLM.
                    # Alternatively, convert to HTML then strip tags, or use a plain text extractor.
                    text_content = markdown_text
                    logger.info(f"Detected Markdown document.")
                except UnicodeDecodeError as e:
                    logger.error(f"Failed to decode Markdown file {filename} as UTF-8: {e}")
                    return None # Indicate decoding failure
            # Add handling for plain text files explicitly
            elif file_ext == ".txt":
                try:
                    text_content = file_content.decode('utf-8')
                    logger.info(f"Detected plain text file (txt).")
                except UnicodeDecodeError as e:
                    logger.error(f"Failed to decode text file {filename} as UTF-8: {e}")
                    return None
            else:
                logger.warning(f"Unsupported file extension '{file_ext}' for file {filename}.")
                # Consider adding ErrorCode.UNSUPPORTED_FILE_TYPE
                # raise DocanalyzerException(*ErrorCode.UNSUPPORTED_FILE_TYPE.value)
                return None # Indicate failure for unsupported types

            logger.info(f"Successfully parsed content from {filename}.")
            # Check if content is empty after parsing
            if not text_content.strip():
                 logger.warning(f"Parsing resulted in empty content for file {filename}.")
                 # Return empty string or None based on desired behavior for empty files
                 # Returning empty string allows processing (e.g., LLM saying "document is empty")
                 # Returning None would trigger the DOCUMENT_PARSING_ERROR earlier

            return text_content.strip() # Return stripped text

        # Specific exception for PDF reading errors
        except pypdf.errors.PdfReadError as e:
             logger.error(f"Failed to parse PDF file {filename} with PyPDF2: {e}")
             return None
        # Catch potential errors from python-docx (e.g., invalid format)
        except Exception as e: # Consider more specific exceptions for docx if available
             # Example check if it's a docx error, though python-docx might raise generic exceptions
             if file_ext == ".docx":
                 logger.error(f"Failed to parse DOCX file {filename}: {e}")
             else:
                 logger.error(f"An unexpected error occurred during parsing of {filename}: {e}")
             return None # Indicate failure


    def _call_llm_for_analysis(self, content: str, criteria: Dict[str, str]) -> Optional[Dict]:
        """Calls the LLM to get feedback and scores based on the content and criteria."""
        if not self.openai_client:
            logger.error("OpenAI client is not initialized. Cannot perform analysis.")
            return None

        # Handle potentially very long content - check token limits? Truncate?
        # This is a basic implementation. Consider token counting & truncation if needed.
        MAX_CHARS = 128000 # Define constant for clarity
        if len(content) > MAX_CHARS:
            logger.warning(f"Content length ({len(content)} chars) is very long. Truncating to {MAX_CHARS} chars for LLM analysis.")
            content = content[:MAX_CHARS] + "\n... [Content Truncated]"

        # Handle empty content explicitly before calling LLM
        if not content.strip():
             logger.warning("Parsed content is empty. Returning minimal analysis result.")
             # Return a default structure indicating no analysis could be performed on content
             return {
                 "feedback": "The document appears to be empty or could not be read properly. No analysis performed.",
                 "scores": {key: 0 for key in criteria.keys()} # Assign 0 scores for empty doc
             }

        criteria_str = "\n".join([f"- {k}: {v}" for k, v in criteria.items()])
        prompt = f"""
Please act as a teaching assistant. Analyze the following document content based on the provided criteria.

**Document Content:**
{content}

**Grading Criteria:**
{criteria_str}

**Instructions:**
1. Provide constructive, specific feedback addressing strengths and weaknesses based on the criteria. If the document content is empty or very short, state that analysis is limited.
2. For each criterion listed above, provide a score from 0 to 100. Assign lower scores (e.g., 0) if the content is insufficient for evaluation.
3. Format your response as a JSON object with two keys: 'feedback' (string) and 'scores' (a dictionary where keys are the criteria names and values are the scores).
   Example JSON format: {{"feedback": "Overall feedback here...", "scores": {{"Clarity": 85, "Correctness": 92, ...}}}}

**Response (JSON format only):**
"""

        try:
            logger.info("Sending request to OpenAI API...")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Or your preferred model
                messages=[
                    {"role": "system",
                     "content": "You are a helpful teaching assistant providing document feedback and grading."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,  # Adjust for creativity vs. consistency
                response_format={"type": "json_object"}  # Ensure JSON output if using compatible models
            )
            response_content = response.choices[0].message.content
            logger.info("Received response from OpenAI API.")

            # Parse the JSON response from the LLM
            analysis_result = json.loads(response_content)

            # Basic validation of the received structure
            if 'feedback' not in analysis_result or 'scores' not in analysis_result:
                logger.error("LLM response did not contain expected 'feedback' and 'scores' keys.")
                return None
            if not isinstance(analysis_result['scores'], dict):
                logger.error("LLM response 'scores' is not a dictionary.")
                return None
            # Optional: Validate scores format further (e.g., ensure they are numbers)

            return analysis_result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from LLM: {e}. Response content: {response_content}")
            return None
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return None
