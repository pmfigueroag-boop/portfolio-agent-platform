from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
import os

API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(api_key_header: str = Security(api_key_header)):
    if not api_key_header:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials"
        )
    
    SECRET_KEY = os.getenv("API_KEY_SECRET", "dev_secret_key")
    if api_key_header != SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    return api_key_header
