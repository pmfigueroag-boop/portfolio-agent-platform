from services.consensus_agent.schema import ConsensusInput, ConsensusOutput
from services.shared.models.enums import SignalType

def aggregate_signals(data: ConsensusInput) -> ConsensusOutput:
    total_score = 0.0
    total_weight = 0.0
    
    for s in data.signals:
        # User shared Enum method to get score
        score = s.signal.to_score()
        
        total_score += score * s.weight
        total_weight += s.weight
        
    final_score = total_score / total_weight if total_weight > 0 else 0.0
    
    # Decision Thresholds
    final_signal = SignalType.HOLD
    
    if final_score > 0.4:
        final_signal = SignalType.BUY
    elif final_score > 0.7: 
        final_signal = SignalType.STRONG_BUY
    elif final_score < -0.4:
        final_signal = SignalType.SELL
    elif final_score < -0.7:
        final_signal = SignalType.STRONG_SELL
        
    confidence = abs(final_score)
    
    return ConsensusOutput(
        ticker=data.ticker,
        final_signal=final_signal,
        confidence_score=round(confidence, 2),
        details={
            "raw_score": round(final_score, 2),
            "agents_count": float(len(data.signals))
        }
    )
