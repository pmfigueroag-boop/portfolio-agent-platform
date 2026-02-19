from fastapi.testclient import TestClient
from services.value_agent.main import app
import time

client = TestClient(app)

def test_rate_limit_exceeded():
    # Limit is 5 per 1 second in code
    
    # 1. Burst 5 requests (Should pass)
    for i in range(5):
        response = client.get("/health")
        assert response.status_code == 200, f"Request {i+1} failed"

    # 2. 6th Request (Should fail)
    response = client.get("/health")
    assert response.status_code == 429
    assert response.text == "Rate limit exceeded"

def test_rate_limit_recovery():
    # Wait for window to reset (1.1s > 1s)
    time.sleep(1.1)
    
    # Should pass again
    response = client.get("/health")
    assert response.status_code == 200
