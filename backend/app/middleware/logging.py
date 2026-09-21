import logging
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("app.middleware.logging")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    HTTP Middleware that logs request/response telemetry,
    including completion latency and response status codes.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()
        
        # Log request receipt
        logger.info(f"Incoming: {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}")
        
        try:
            response = await call_next(request)
            
            process_time = (time.perf_counter() - start_time) * 1000
            logger.info(
                f"Outgoing: {request.method} {request.url.path} - Status: {response.status_code} - "
                f"Latency: {process_time:.2f}ms"
            )
            return response
            
        except Exception as e:
            process_time = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Failed: {request.method} {request.url.path} - Exception: {str(e)} - "
                f"Latency: {process_time:.2f}ms"
            )
            # Re-raise the exception to be caught by the global exception handler
            raise e
