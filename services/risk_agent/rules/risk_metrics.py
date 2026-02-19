import pandas as pd
import numpy as np
from services.risk_agent.schema import RiskInput, RiskOutput

def calculate_risk_metrics(data: RiskInput) -> RiskOutput:
    # No need to check length < 30 due to Pydantic validator
    
    df = pd.DataFrame([p.dict() for p in data.prices])
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').set_index('date')
    
    # 1. Max Drawdown
    # Protection against zero division is handled by schema gt=0 on price
    cumulative_returns = (1 + df['price'].pct_change().fillna(0)).cumprod()
    peak = cumulative_returns.expanding(min_periods=1).max()
    
    # Avoid division by zero if peak is somehow 0 (impossible with positive prices)
    drawdown = (cumulative_returns / peak) - 1
    max_drawdown = drawdown.min()
    
    # 2. Volatility
    daily_returns = df['price'].pct_change().dropna()
    if daily_returns.empty:
        annualized_vol = 0.0
    else:
        annualized_vol = daily_returns.std() * np.sqrt(252)
    
    # 3. Risk Adjustment
    target_vol = data.target_volatility
    
    if annualized_vol < 1e-6: # Prevent division by zero logic
        exposure = 1.0 # No volatility? Full exposure (theoretical)
    else:
        exposure = target_vol / annualized_vol
        
    exposure = min(exposure, 1.0)
    
    if max_drawdown < -0.20:
        exposure = exposure * 0.5
        
    return RiskOutput(
        max_drawdown=round(float(max_drawdown), 4),
        volatility=round(float(annualized_vol), 4),
        risk_adjusted_exposure=round(float(exposure), 2),
        details={
            "drawdown_warning": bool(max_drawdown < -0.15),
            "volatility_warning": bool(annualized_vol > target_vol)
        }
    )
