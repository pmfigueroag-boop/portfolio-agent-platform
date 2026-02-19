from fastapi import APIRouter, HTTPException
from services.risk_agent.schema import RiskInput, RiskOutput
from services.risk_agent.rules.risk_metrics import calculate_risk_metrics
from services.shared.logger import setup_logger

from services.shared.security import get_api_key

router = APIRouter()
logger = setup_logger("risk_agent")

@router.post("/analyze", response_model=RiskOutput, dependencies=[Depends(get_api_key)])
async def analyze_risk(data: RiskInput):
    logger.info(f"Analyzing risk for {len(data.prices)} price points")
    try:
        result = calculate_risk_metrics(data)
        logger.info(f"Risk analysis complete: DD={result.max_drawdown}, Vol={result.volatility}")
        return result
    except Exception as e:
        logger.error(f"Error analyzing risk: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "ok"}
