from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime
from services.shared.models.enums import SignalType

class PricePoint(BaseModel):
    date: datetime
    price: float = Field(..., gt=0)

class QuantInput(BaseModel):
    ticker: str = Field(..., min_length=1)
    prices: List[PricePoint] = Field(..., min_length=30, description="Minimum 30 days of data required")

class QuantOutput(BaseModel):
    ticker: str
    momentum_score: float
    volatility: float
    signal: SignalType
    details: Dict[str, float]
