from utils.error_code import ErrorCode


class DocanalyzerException(Exception):
    code: int
    message: str

    def __init__(self, error_code=None, message=None, code=None):
        if isinstance(error_code, ErrorCode):
            self.code = error_code.code
            # If a message is provided, append it to the error code's message
            self.message = error_code.message if message is None else f"{error_code.message}: {message}"
        elif code is not None and message is not None:
            self.code = code
            self.message = message
        else:
            # Handle invalid arguments, or set default values
            self.code = 500
            self.message = "An unexpected error occurred"
        super().__init__(self.message)
