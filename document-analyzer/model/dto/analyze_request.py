from pydantic import BaseModel, Field
from typing import Optional, Dict, List

class AnalyzeRequest(BaseModel):
    """
    Request DTO for document analysis. This DTO might become empty or removed 
    if all parameters are passed via Form data with UploadFile.
    Keeping it for structure for now, potentially remove later.
    """
    pass # No fields needed here if file and criteria are passed via Form/File