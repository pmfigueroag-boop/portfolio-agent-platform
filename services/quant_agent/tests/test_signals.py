import pytest
from datetime import datetime, timedelta
from services.quant_agent.schema import QuantInput, PricePoint
from services.quant_agent.rules.signals import calculate_quant_signals
from services.shared.models.enums import SignalType
from pydantic import ValidationError

def generate_prices(trend="UP", volatility="LOW", days=100):
    prices = []
    base_price = 100.0
    for i in range(days):
        date = datetime.now() - timedelta(days=days-i)
        change = 0.005 if trend == "UP" else -0.005
        noise = (i % 2) * 0.001 if volatility == "LOW" else (i % 2) * 0.02
        base_price = base_price * (1 + change + noise)
        # Ensure price > 0
        base_price = max(base_price, 0.01)
        prices.append(PricePoint(date=date, price=base_price))
    return prices

def test_quant_buy_signal():
    prices = generate_prices(trend="UP", volatility="LOW", days=250)
    data = QuantInput(ticker="GOOD", prices=prices)
    result = calculate_quant_signals(data)
    assert result.signal == SignalType.BUY
    assert result.momentum_score > 0

def test_insufficient_data_validation():
    prices = generate_prices(days=10) # Too few
    with pytest.raises(ValidationError):
        QuantInput(ticker="SHORT", prices=prices)
