# Document Analyzer API

API for analyzing documents using LLMs, providing feedback and scores.

## API Documentation

### Analyze Document

Analyzes the provided document based on optional criteria.

- **URL**: `/v1/analyzer/document`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`

**Request Body:**

- `file`: (Required) The document file to be analyzed. pdf, md, docx, or txt.
- `filename`: (Required) The filename of the uploaded document.
- `criteria`: (Optional) A JSON string representing custom grading criteria. Example: `{"clarity": "Is the document clear?", "completeness": "Does the document cover all required points?"}`

**Example Request (using cURL):**

```bash
curl -X POST "http://localhost:8000/v1/analyzer/document" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@/path/to/your/document.txt" \
     -F "filename=document.txt" \
     -F "criteria={\"grammar\": \"Check for grammatical errors\"}"
```

**Successful Response (200 OK):**

```json
{
    "code": 200,
    "message": "Success",
    "data": {
        "feedback": "",
        "scores": {
            "Clarity": 0.0,
            "Correctness": 0.0,
            "Completeness": 0.0,
            "Structure": 0.0,
            "Engagement": 0.0
        },
        "overall_score": 0.0,
        "parsed_content": null
    }
}
```

## Getting Started

### Prerequisites

- Docker

### Build the Docker Image

```bash
docker build -t document-analyzer:main .
```

### Run the Docker Container

Ensure you have a `.env` file in the project root with necessary environment variables (e.g., API keys for LLMs).

```bash
# Make sure your .env file is in the current directory or provide the full path
docker run --env-file .env -p 8000:80 document-analyzer:main
```

The API will be accessible at `http://localhost:8000`. 