from enum import Enum


class ErrorCode(Enum):
    BAD_REQUEST = (400, "Bad request")
    UNAUTHORIZED = (401, "Unauthorized")
    NOT_FOUND = (404, "Item not found")
    INTERNAL_SERVER_ERROR = (500, "Internal server error")
    DOCUMENT_PARSING_ERROR = (500, "Document parsing error")
    LLM_ANALYSIS_ERROR = (500, "LLM analysis error")
    FILE_READ_ERROR = (500, "File read error")
    INVALID_CRITERIA_FORMAT = (400, "Invalid criteria format")
    # Add more as needed...

    @property
    def code(self):
        return self.value[0]

    @property
    def message(self):
        return self.value[1]
