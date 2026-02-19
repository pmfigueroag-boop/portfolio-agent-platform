from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from services.shared.models.enums import SignalType

class AgentSignal(BaseModel):
    agent_name: str = Field(..., min_length=1)
    signal: SignalType # Strict Enum validation
    score: Optional[float] = Field(0.0, ge=-1.0, le=1.0)
    weight: float = Field(1.0, gt=0)

class ConsensusInput(BaseModel):
    ticker: str = Field(..., min_length=1)
    signals: List[AgentSignal] = Field(..., min_length=1)

class ConsensusOutput(BaseModel):
    ticker: str
    final_signal: SignalType
    confidence_score: float
    details: Dict[str, float]
