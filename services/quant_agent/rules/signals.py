import pandas as pd
import numpy as np
from services.quant_agent.schema import QuantInput, QuantOutput
from services.shared.models.enums import SignalType

def calculate_quant_signals(data: QuantInput) -> QuantOutput:
    # Schema validation ensures min_length=30, so no need to check empty here
    
    df = pd.DataFrame([p.dict() for p in data.prices])
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').set_index('date')
    
    # 1. Momentum
    current_price = df['price'].iloc[-1]
    price_30d_ago = df['price'].iloc[-30]
    
    momentum_30d = (current_price - price_30d_ago) / price_30d_ago
    
    # 2. Volatility
    df['returns'] = df['price'].pct_change().dropna()
    if df['returns'].empty:
        daily_vol = 0.0
    else:
        daily_vol = df['returns'].std()
        
    annualized_vol = daily_vol * np.sqrt(252)
    
    # 3. Moving Averages
    ma_50 = df['price'].rolling(window=50).mean().iloc[-1] if len(df) >= 50 else current_price
    ma_200 = df['price'].rolling(window=200).mean().iloc[-1] if len(df) >= 200 else current_price
    
    # 4. Decision Logic
    signal = SignalType.HOLD
    score = 0
    
    if momentum_30d > 0.05 and current_price > ma_50:
        score += 1
    if current_price > ma_200:
        score += 1
    if annualized_vol < 0.20:
        score += 1
        
    if score >= 2:
        signal = SignalType.BUY
    elif momentum_30d < -0.05 or current_price < ma_200:
        signal = SignalType.SELL
        
    return QuantOutput(
        ticker=data.ticker,
        momentum_score=round(momentum_30d, 4),
        volatility=round(annualized_vol, 4),
        signal=signal,
        details={
            "ma_50": round(ma_50, 2),
            "ma_200": round(ma_200, 2),
            "score": float(score)
        }
    )
