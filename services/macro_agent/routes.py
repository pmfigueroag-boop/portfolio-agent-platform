from fastapi import APIRouter, HTTPException
from services.macro_agent.schema import MacroInput, MacroOutput
from services.macro_agent.rules.macro_analysis import analyze_macro_regime
from services.shared.logger import setup_logger

from services.shared.security import get_api_key

router = APIRouter()
logger = setup_logger("macro_agent")

@router.post("/analyze", response_model=MacroOutput, dependencies=[Depends(get_api_key)])
async def analyze_macro(data: MacroInput):
    logger.info(f"Analyzing macro data: GDP={data.gdp_growth}, Infl={data.inflation_rate}")
    try:
        result = analyze_macro_regime(data)
        logger.info(f"Macro analysis complete: {result.regime} -> {result.signal}")
        return result
    except Exception as e:
        logger.error(f"Error in macro analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "ok"}
