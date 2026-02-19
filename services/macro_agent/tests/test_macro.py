import pytest
from services.macro_agent.schema import MacroInput
from services.macro_agent.rules.macro_analysis import analyze_macro_regime
from services.shared.models.enums import SignalType

def test_goldilocks_regime():
    data = MacroInput(
        inflation_rate=0.02,
        interest_rate=0.03,
        gdp_growth=0.03,
        unemployment_rate=0.04,
        liquidity_index=0.10
    )
    result = analyze_macro_regime(data)
    assert result.regime == "Goldilocks"
    assert result.signal == SignalType.RISK_ON

def test_stagflation_regime():
    data = MacroInput(
        inflation_rate=0.06,
        interest_rate=0.02,
        gdp_growth=0.01,
        unemployment_rate=0.06,
        liquidity_index=0.05
    )
    result = analyze_macro_regime(data)
    assert result.regime == "Stagflation"
    assert result.signal == SignalType.RISK_OFF
