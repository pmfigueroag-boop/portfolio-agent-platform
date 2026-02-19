import pytest
from services.consensus_agent.schema import ConsensusInput, AgentSignal
from services.consensus_agent.rules.aggregation import aggregate_signals
from services.shared.models.enums import SignalType

def test_consensus_buy():
    data = ConsensusInput(
        ticker="GOOD",
        signals=[
            AgentSignal(agent_name="Value", signal=SignalType.BUY, weight=1.0),
            AgentSignal(agent_name="Quant", signal=SignalType.BUY, weight=1.0),
            AgentSignal(agent_name="Macro", signal=SignalType.RISK_ON, weight=0.5),
            AgentSignal(agent_name="Risk", signal=SignalType.HOLD, weight=0.5)
        ]
    )
    result = aggregate_signals(data)
    # Logic check: 0.5 + 0.5 + 0.25 + 0 = 1.25 / 3.0 = 0.416 > 0.4 -> BUY
    assert result.final_signal == SignalType.BUY
    assert result.confidence_score > 0.4

def test_consensus_sell():
    data = ConsensusInput(
        ticker="BAD",
        signals=[
            AgentSignal(agent_name="Value", signal=SignalType.SELL, weight=1.0), # -0.5
            AgentSignal(agent_name="Quant", signal=SignalType.SELL, weight=1.0), # -0.5
            AgentSignal(agent_name="Macro", signal=SignalType.RISK_OFF, weight=0.5) # -0.25
        ]
    )
    # Score: -1.25 / 2.5 = -0.5 < -0.4 -> SELL
    result = aggregate_signals(data)
    assert result.final_signal == SignalType.SELL
