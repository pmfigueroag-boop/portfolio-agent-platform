from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class PricePoint(BaseModel):
    date: datetime
    price: float = Field(..., gt=0)

class RiskInput(BaseModel):
    prices: List[PricePoint] = Field(..., min_length=30)
    target_volatility: float = Field(0.15, gt=0, le=1.0) 

class RiskOutput(BaseModel):
    max_drawdown: float
    volatility: float
    risk_adjusted_exposure: float = Field(..., ge=0.0, le=1.0)
    details: Dict[str, bool]
