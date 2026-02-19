import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def add_cors_middleware(app: FastAPI):
    # Security: Allow origins from env, split by comma. 
    # Default to localhost for dev compatibility, but explicit is better.
    origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000")
    
    origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], # Explicit methods
        allow_headers=["*"], # Headers can usually remain broad for APIs
    )
