from services.value_agent.schema import ValuationInput, ValuationOutput
from services.shared.models.enums import SignalType

def calculate_intrinsic_value(data: ValuationInput) -> ValuationOutput:
    # 1. Simple DCF approximation
    growth_rate = min(data.roe * 0.5, 0.15) 
    discount_rate = 0.10
    
    current_fcf = data.fcf
    total_present_value = 0.0
    
    # 5 Year Projection
    for i in range(1, 6):
        current_fcf *= (1 + growth_rate)
        total_present_value += current_fcf / ((1 + discount_rate) ** i)
        
    # Terminal Value
    terminal_value = (current_fcf * 1.02) / (discount_rate - 0.02)
    discounted_terminal = terminal_value / ((1 + discount_rate) ** 5)
    
    total_enterprise_value = total_present_value + discounted_terminal
    equity_value = total_enterprise_value - data.debt
    intrinsic_per_share = equity_value / data.shares_outstanding
    
    # Avoid division by zero if intrinsic value is zero (unlikely but safe)
    if intrinsic_per_share <= 0:
        margin_of_safety = -1.0 # Deeply negative / overvalued
    else:
        margin_of_safety = (intrinsic_per_share - data.current_price) / intrinsic_per_share
    
    # 2. Deuda/EBITDA Check
    debt_to_ebitda = data.debt / data.ebitda
    
    # 3. Decision Logic
    signal = SignalType.HOLD
    
    if margin_of_safety > 0.40 and debt_to_ebitda < 2.5:
        signal = SignalType.STRONG_BUY
    elif margin_of_safety > 0.20 and debt_to_ebitda < 3.5:
        signal = SignalType.BUY
    elif margin_of_safety < -0.20 or debt_to_ebitda > 5.0:
        signal = SignalType.SELL # Interpreted as Avoid/Sell
        
    return ValuationOutput(
        ticker=data.ticker,
        intrinsic_value=round(intrinsic_per_share, 2),
        margin_of_safety=round(margin_of_safety, 2),
        signal=signal,
        details={
            "debt_to_ebitda": round(debt_to_ebitda, 2),
            "assumed_growth": round(growth_rate, 2),
            "equity_value": round(equity_value, 2)
        }
    )
