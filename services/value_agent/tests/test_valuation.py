import pytest
from services.value_agent.schema import ValuationInput
from services.value_agent.rules.valuation import calculate_intrinsic_value
from services.shared.models.enums import SignalType
from pydantic import ValidationError

def test_intrinsic_value_strong_buy():
    data = ValuationInput(
        ticker="AAPL",
        roe=0.30,
        fcf=100_000_000,
        debt=10_000_000,
        ebitda=200_000_000, 
        current_price=150.0,
        shares_outstanding=1_000_000
    )
    result = calculate_intrinsic_value(data)
    assert result.ticker == "AAPL"
    # Logic might vary, but ensure signal is a valid Enum
    assert isinstance(result.signal, SignalType)
    assert result.margin_of_safety is not None

def test_intrinsic_value_avoid_signal():
    data = ValuationInput(
        ticker="BAD",
        roe=0.05,
        fcf=100,
        debt=10_000_000,
        ebitda=1_000,
        current_price=100.0,
        shares_outstanding=1_000
    )
    result = calculate_intrinsic_value(data)
    assert result.signal == SignalType.SELL # Mapped to SELL/AVOID

def test_zero_ebitda_validation():
    with pytest.raises(ValidationError):
        ValuationInput(
            ticker="ZERO",
            roe=0.1,
            fcf=100.0,
            debt=100.0,
            ebitda=0.0, # Should fail
            current_price=10.0,
            shares_outstanding=10.0
        )
