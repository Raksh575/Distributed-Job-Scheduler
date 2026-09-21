import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Fast, thread-safe, in-memory sliding window rate limiter.
    Limits clients to 100 requests per minute per IP address.
    """
    def __init__(self, app, limit: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Resolve client IP
        client_ip = request.client.host if request.client else "unknown-ip"
        
        # Bypass options for WebSocket handshakes or specific local routes
        if request.url.path.startswith("/ws"):
            return await call_next(request)
            
        now = time.time()
        
        # Filter request timestamps older than the sliding window
        window_start = now - self.window_seconds
        client_history = self.requests[client_ip]
        client_history = [t for t in client_history if t > window_start]
        self.requests[client_ip] = client_history
        
        # Check limit threshold
        if len(client_history) >= self.limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "message": "Too many requests. Please slow down and try again.",
                        "code": "RATE_LIMIT_EXCEEDED",
                        "retry_after_seconds": int(self.window_seconds - (now - client_history[0]))
                    }
                }
            )
            
        # Record current request
        self.requests[client_ip].append(now)
        
        return await call_next(request)
