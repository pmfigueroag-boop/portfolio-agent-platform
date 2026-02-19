from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int = 100, window: int = 60):
        """
        Simple In-Memory Rate Limiter.
        :param limit: Max requests per window
        :param window: Window execution time in seconds
        """
        super().__init__(app)
        self.limit = limit
        self.window = window
        # Storage: IP -> list of timestamps
        # In production, use Redis!
        self.request_history = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()
        
        # Clean old requests
        self.request_history[client_ip] = [
            t for t in self.request_history[client_ip] 
            if t > now - self.window
        ]
        
        # Check limit
        if len(self.request_history[client_ip]) >= self.limit:
            return Response("Rate limit exceeded", status_code=429)
            
        self.request_history[client_ip].append(now)
        
        return await call_next(request)
