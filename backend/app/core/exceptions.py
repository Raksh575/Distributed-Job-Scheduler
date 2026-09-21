from typing import Any, Dict, Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

class AppException(Exception):
    """Base application exception for Custom domain errors."""
    def __init__(
        self, 
        message: str, 
        code: str = "INTERNAL_SERVER_ERROR", 
        status_code: int = HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

class NotFoundException(AppException):
    def __init__(self, message: str, code: str = "NOT_FOUND", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, HTTP_404_NOT_FOUND, details)

class UnauthorizedException(AppException):
    def __init__(self, message: str, code: str = "UNAUTHORIZED", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, HTTP_401_UNAUTHORIZED, details)

class ForbiddenException(AppException):
    def __init__(self, message: str, code: str = "FORBIDDEN", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, HTTP_403_FORBIDDEN, details)

class BadRequestException(AppException):
    def __init__(self, message: str, code: str = "BAD_REQUEST", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, HTTP_400_BAD_REQUEST, details)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Log original exception details internally
    # We canimport logger dynamically to log
    import logging
    logger = logging.getLogger("app.exceptions")
    logger.exception(f"Unhandled system error encountered: {str(exc)}")
    
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred on the server.",
                "details": {}
            }
        }
    )

def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
