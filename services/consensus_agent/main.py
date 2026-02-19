from fastapi import FastAPI
from services.consensus_agent.routes import router
from services.shared.config import settings
from services.shared.middleware import add_cors_middleware

app = FastAPI(
    title="Consensus Agent",
    description="Microservice for Signal Aggregation and Final Decision",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

add_cors_middleware(app)

app.include_router(router, prefix="/api/v1/consensus", tags=["consensus"])

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/ready")
def readiness_check():
    from services.shared.database import SessionLocal
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        return {"status": "ready"}
    except Exception:
        return {"status": "not_ready"}, 503
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
