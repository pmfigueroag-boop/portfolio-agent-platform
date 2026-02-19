import pytest
from datetime import datetime, timedelta
from services.risk_agent.schema import RiskInput, PricePoint
from services.risk_agent.rules.risk_metrics import calculate_risk_metrics

def generate_prices(volatility="LOW", crash=False, days=100):
    prices = []
    base_price = 100.0
    for i in range(days):
        date = datetime.now() - timedelta(days=days-i)
        change = 0.0005
        if crash and i > days - 10:
            change = -0.05
        noise = (i % 2) * 0.001 if volatility == "LOW" else (i % 2) * 0.02
        base_price = base_price * (1 + change + noise)
        prices.append(PricePoint(date=date, price=base_price))
    return prices

def test_risk_low_vol():
    prices = generate_prices(volatility="LOW", days=250)
    data = RiskInput(prices=prices, target_volatility=0.15)
    result = calculate_risk_metrics(data)
    assert result.volatility < 0.15
    assert result.risk_adjusted_exposure >= 1.0

def test_risk_crash_drawdown():
    prices = generate_prices(volatility="HIGH", crash=True, days=250)
    data = RiskInput(prices=prices)
    result = calculate_risk_metrics(data)
    assert result.max_drawdown < -0.20
    assert result.risk_adjusted_exposure < 1.0
