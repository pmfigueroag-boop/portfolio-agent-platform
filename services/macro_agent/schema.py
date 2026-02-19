from pydantic import BaseModel, Field
from typing import Dict
from services.shared.models.enums import SignalType

class MacroInput(BaseModel):
    inflation_rate: float
    interest_rate: float
    gdp_growth: float
    unemployment_rate: float = Field(..., ge=0, le=1)
    liquidity_index: float

class MacroOutput(BaseModel):
    regime: str
    signal: SignalType
    details: Dict[str, bool]
