from fastapi import APIRouter, HTTPException, Depends
from services.value_agent.schema import ValuationInput, ValuationOutput
from services.value_agent.rules.valuation import calculate_intrinsic_value
from services.shared.logger import setup_logger

from services.shared.security import get_api_key

router = APIRouter()
logger = setup_logger("value_agent")

@router.post("/analyze", response_model=ValuationOutput, dependencies=[Depends(get_api_key)])
async def analyze_stock(data: ValuationInput):
    logger.info(f"Analyzing ticker: {data.ticker}")
    try:
        result = calculate_intrinsic_value(data)
        logger.info(f"Analysis complete for {data.ticker}: {result.signal}")
        return result
    except Exception as e:
        logger.error(f"Error analyzing {data.ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "ok"}
