from services.macro_agent.schema import MacroInput, MacroOutput
from services.shared.models.enums import SignalType

def analyze_macro_regime(data: MacroInput) -> MacroOutput:
    # 1. Determine Regime
    regime = "Neutral"
    
    high_growth = data.gdp_growth > 0.02
    high_inflation = data.inflation_rate > 0.03
    
    if high_growth and not high_inflation:
        regime = "Goldilocks"
    elif high_growth and high_inflation:
        regime = "Overheating" 
    elif not high_growth and high_inflation:
        regime = "Stagflation"
    elif not high_growth and not high_inflation:
        regime = "Recession"
        
    # 2. Determine Signal 
    signal = SignalType.NEUTRAL
    
    if regime == "Goldilocks":
        signal = SignalType.RISK_ON
    elif regime == "Overheating":
        if data.interest_rate > 0.05: 
            signal = SignalType.NEUTRAL
        else:
            signal = SignalType.RISK_ON
    elif regime == "Stagflation":
        signal = SignalType.RISK_OFF
    elif regime == "Recession":
        if data.liquidity_index > 0.05: 
            signal = SignalType.NEUTRAL 
        else:
            signal = SignalType.RISK_OFF
            
    return MacroOutput(
        regime=regime,
        signal=signal,
        details={
            "inflation_tolerance_exceeded": high_inflation,
            "growth_target_met": high_growth
        }
    )
