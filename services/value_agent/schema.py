from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict
from services.shared.models.enums import SignalType

class ValuationInput(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10)
    roe: float
    fcf: float
    debt: float = Field(..., ge=0)
    ebitda: float
    current_price: float = Field(..., gt=0)
    shares_outstanding: float = Field(..., gt=0)

    @field_validator('ebitda')
    def prevent_zero_ebitda(cls, v):
        if v == 0:
            raise ValueError("EBITDA cannot be exactly zero")
        return v

class ValuationOutput(BaseModel):
    ticker: str
    intrinsic_value: float
    margin_of_safety: float
    signal: SignalType
    details: Dict[str, float]
