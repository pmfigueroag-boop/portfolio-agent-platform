from fastapi import APIRouter, HTTPException
from services.quant_agent.schema import QuantInput, QuantOutput
from services.quant_agent.rules.signals import calculate_quant_signals
from services.shared.logger import setup_logger

from services.shared.security import get_api_key

router = APIRouter()
logger = setup_logger("quant_agent")

@router.post("/analyze", response_model=QuantOutput, dependencies=[Depends(get_api_key)])
async def analyze_quant(data: QuantInput):
    logger.info(f"Analyzing ticker: {data.ticker} with {len(data.prices)} price points")
    try:
        result = calculate_quant_signals(data)
        logger.info(f"Analysis complete for {data.ticker}: {result.signal}")
        return result
    except Exception as e:
        logger.error(f"Error analyzing {data.ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "ok"}
