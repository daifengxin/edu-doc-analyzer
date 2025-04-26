import json
from typing import Optional, Dict

from fastapi import APIRouter, Depends, UploadFile, File, Form

from service.analyzer_service import AnalyzerService
from utils.response import DocanalyzerResponse, response_formatter
from utils.logger import logger
from utils.exception import DocanalyzerException
from utils.error_code import ErrorCode

analyzer_router = APIRouter(prefix="/v1/analyzer", tags=["Analyzer"])

@analyzer_router.post("/document", response_model=DocanalyzerResponse)
async def analyze_document_endpoint(
    file: UploadFile = File(..., description="Document file to be analyzed."),
    filename: str = Form(..., description="Filename of the uploaded document."),
    criteria: Optional[str] = Form(None, description="Optional custom grading criteria as a JSON string. E.g., '{\"clarity\": \"Is the document clear?\"}'"),
    service: AnalyzerService = Depends()
):
    try:
        file_content = await file.read()
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {e}")
        raise DocanalyzerException(*ErrorCode.FILE_READ_ERROR.value)
    finally:
        await file.close()

    parsed_criteria: Optional[Dict[str, str]] = None
    if criteria:
        try:
            parsed_criteria = json.loads(criteria)
            if not isinstance(parsed_criteria, dict):
                raise DocanalyzerException(*ErrorCode.INVALID_CRITERIA_FORMAT.value, message="Criteria must be a valid JSON object string.")
        except json.JSONDecodeError:
            raise DocanalyzerException(*ErrorCode.INVALID_CRITERIA_FORMAT.value, message="Criteria is not a valid JSON string.")
        except DocanalyzerException as e:
            raise e
        except Exception as e:
            logger.error(f"Failed to parse criteria JSON: {e}")
            raise DocanalyzerException(*ErrorCode.INVALID_CRITERIA_FORMAT.value)

    return response_formatter(await service.analyze_document(file_content=file_content, filename=filename, criteria=parsed_criteria))
