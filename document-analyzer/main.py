from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
# Import the analyzer router
from controller.v1.analyzer_controller import analyzer_router

from utils.error_code import ErrorCode
from utils.logger import logger
from utils.exception import DocanalyzerException
from utils.response import error_response

app = FastAPI(
    title="Document Analyzer API",
    description="API for analyzing documents using LLMs, providing feedback and scores.",
    version="1.0.0"
)

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, etc.)
    allow_headers=["*"], # Allow all headers
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log the incoming request
    logger.info(f"Incoming request: {request.method} {request.url}")
    # Log headers if needed (be careful with sensitive info)
    # logger.debug(f"Headers: {request.headers}")
    # Log body if needed (can be large or sensitive, use with caution)
    # try:
    #     body = await request.body()
    #     logger.debug(f"Body: {body.decode()}")
    #     # Need to make the body available again for the endpoint
    #     request._body = body 
    # except Exception:
    #     logger.warning("Could not log request body.")
        
    start_time = datetime.now()

    # Process the request
    response = await call_next(request)

    # Log the outgoing response
    process_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"Outgoing response: {response.status_code} - Processed in {process_time:.4f} sec")
    return response


@app.exception_handler(DocanalyzerException)
async def docanalyzer_exception_handler(request: Request, exc: DocanalyzerException):
    logger.error(f"Docanalyzer Exception: {exc.message} (Code: {exc.code})", exc_info=False) # Log less verbosely by default for known exceptions
    # Optionally log traceback if needed for specific error codes or debugging
    # if exc.code >= 500:
    #    logger.exception(f"Docanalyzer Exception Traceback:") 
    return JSONResponse(
        status_code=exc.code if exc.code >=400 and exc.code < 600 else 500, # Ensure valid HTTP status code range
        content=error_response(exc.code, exc.message),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled Exception: {str(exc)}") # Log full traceback for unexpected errors
    # Return a generic 500 error using the defined structure
    error_info = ErrorCode.INTERNAL_SERVER_ERROR.value
    return JSONResponse(
        status_code=ErrorCode.INTERNAL_SERVER_ERROR.code, # Use code from Enum
        content=error_response(error_info[0], error_info[1])
    )

# Include the analyzer router
app.include_router(analyzer_router)

# Add a root endpoint for health check or basic info
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Document Analyzer API"}

# Add the Uvicorn run block for direct execution
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Document Analyzer API...")
    # Use reload=True for development, remove or set to False for production
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

