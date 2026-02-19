from enum import Enum

class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    
    # Macro Specific
    RISK_ON = "RISK_ON"
    RISK_OFF = "RISK_OFF"
    NEUTRAL = "NEUTRAL"
    
    # Strong signals
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"
    
    def to_score(self) -> float:
        mapping = {
            SignalType.STRONG_BUY: 1.0,
            SignalType.BUY: 0.5,
            SignalType.RISK_ON: 0.5,
            SignalType.HOLD: 0.0,
            SignalType.NEUTRAL: 0.0,
            SignalType.RISK_OFF: -0.5,
            SignalType.SELL: -0.5,
            SignalType.STRONG_SELL: -1.0
        }
        return mapping.get(self, 0.0)
