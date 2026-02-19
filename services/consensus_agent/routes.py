from fastapi import APIRouter, HTTPException
from services.consensus_agent.schema import ConsensusInput, ConsensusOutput
from services.consensus_agent.rules.aggregation import aggregate_signals
from services.shared.logger import setup_logger

router = APIRouter()
logger = setup_logger("consensus_agent")

@router.post("/decide", response_model=ConsensusOutput)
async def reach_consensus(data: ConsensusInput):
    logger.info(f"Aggregating signals for {data.ticker} from {len(data.signals)} agents")
    try:
        result = aggregate_signals(data)
        logger.info(f"Consensus reached for {data.ticker}: {result.final_signal} (Conf: {result.confidence_score})")
        return result
    except Exception as e:
        logger.error(f"Error in consensus: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "ok"}
