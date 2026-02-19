import requests
import json
import os
from sqlalchemy.orm import Session
from datetime import datetime
from services.shared.database import SessionLocal
from services.shared.models.domain import Asset, Price, Fundamental, MacroData, AgentOutput
from services.shared.logger import setup_logger
from services.shared.models.enums import SignalType
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = setup_logger("pipeline")

# Service URLs - support Docker internal networking via env vars
AGENTS = {
    "value": os.getenv("Value_URL", "http://localhost:8001/api/v1/value"),
    "quant": os.getenv("Quant_URL", "http://localhost:8002/api/v1/quant"),
    "macro": os.getenv("Macro_URL", "http://localhost:8003/api/v1/macro"),
    "risk": os.getenv("Risk_URL", "http://localhost:8004/api/v1/risk"),
    "consensus": os.getenv("Consensus_URL", "http://localhost:8005/api/v1/consensus")
}

# Resilience: Retry configuration
# Stop after 3 attempts
# Wait 1s, then 2s, etc.
RETRY_CONFIG = {
    "stop": stop_after_attempt(3),
    "wait": wait_exponential(multiplier=1, min=1, max=10),
    "retry": retry_if_exception_type(requests.exceptions.RequestException)
}

@retry(**RETRY_CONFIG)
def call_agent(url, payload):
    resp = requests.post(url, json=payload, timeout=10) # Added timeout
    resp.raise_for_status()
    return resp.json()

def run_pipeline():
    db = SessionLocal()
    try:
        # 1. Fetch Macro Context
        macro_record = db.query(MacroData).order_by(MacroData.date.desc()).first()
        if not macro_record:
            logger.error("No macro data found. Run seeder first.")
            return

        macro_payload = {
            "inflation_rate": macro_record.inflation_rate,
            "interest_rate": macro_record.interest_rate,
            "gdp_growth": macro_record.gdp_growth,
            "unemployment_rate": macro_record.unemployment_rate,
            "liquidity_index": 0.10 # Stub
        }
        
        logger.info("--- Calling Macro Agent ---")
        try:
            macro_resp = call_agent(f"{AGENTS['macro']}/analyze", macro_payload)
            macro_signal = macro_resp['signal']
            logger.info(f"Macro Signal: {macro_signal}")
        except Exception as e:
            logger.error(f"Macro Agent failed after retries: {e}")
            macro_signal = "NEUTRAL"

        # 2. Iterate Assets
        assets = db.query(Asset).all()
        for asset in assets:
            logger.info(f"Processing Asset: {asset.ticker}")
            
            # Fetch Context Data
            prices = db.query(Price).filter(Price.asset_id == asset.id).order_by(Price.date.asc()).all()
            fundamental = db.query(Fundamental).filter(Fundamental.asset_id == asset.id).order_by(Fundamental.reporting_date.desc()).first()
            
            if not prices or len(prices) < 30:
                logger.warning(f"Skipping {asset.ticker}: Insufficient price data")
                continue
                
            # Prepare Payloads
            price_list = [{"date": p.date.isoformat(), "price": p.close} for p in prices]
            
            agent_signals = []
            
            # --- Value Agent ---
            if fundamental:
                mock_debt = 1_000_000_000.0
                mock_ebitda = mock_debt / fundamental.debt_to_ebitda if fundamental.debt_to_ebitda else 1.0
                
                value_payload = {
                    "ticker": asset.ticker,
                    "roe": fundamental.roe,
                    "fcf": fundamental.fcf,
                    "debt": mock_debt,
                    "ebitda": mock_ebitda,
                    "current_price": prices[-1].close,
                    "shares_outstanding": 100_000_000
                }
                try:
                    res = call_agent(f"{AGENTS['value']}/analyze", value_payload)
                    agent_signals.append({
                        "agent_name": "Value",
                        "signal": res['signal'],
                        "weight": 1.0,
                        "score": 0.0
                    })
                    save_output(db, asset.id, "value_agent", res['signal'], 0.0, res)
                except Exception as e:
                    logger.error(f"Value Agent failed for {asset.ticker}: {e}")

            # --- Quant Agent ---
            quant_payload = {"ticker": asset.ticker, "prices": price_list}
            try:
                res = call_agent(f"{AGENTS['quant']}/analyze", quant_payload)
                agent_signals.append({
                    "agent_name": "Quant",
                    "signal": res['signal'],
                    "weight": 1.0,
                    "score": res['momentum_score'] 
                })
                save_output(db, asset.id, "quant_agent", res['signal'], res['momentum_score'], res)
            except Exception as e:
                 logger.error(f"Quant Agent failed for {asset.ticker}: {e}")

            # --- Risk Agent ---
            risk_payload = {"prices": price_list, "target_volatility": 0.15}
            try:
                res = call_agent(f"{AGENTS['risk']}/analyze", risk_payload)
                risk_sig = SignalType.HOLD
                if res['risk_adjusted_exposure'] < 0.5:
                    risk_sig = SignalType.SELL
                elif res['risk_adjusted_exposure'] >= 0.9:
                    risk_sig = SignalType.BUY
                    
                agent_signals.append({
                    "agent_name": "Risk",
                    "signal": risk_sig, 
                    "weight": 1.5,
                    "score": res['risk_adjusted_exposure']
                })
                save_output(db, asset.id, "risk_agent", str(risk_sig), res['risk_adjusted_exposure'], res)
            except Exception as e:
                 logger.error(f"Risk Agent failed for {asset.ticker}: {e}")
            
            # --- Include Macro Signal ---
            agent_signals.append({
                 "agent_name": "Macro",
                 "signal": macro_signal,
                 "weight": 0.5,
                 "score": 0.0
            })

            # --- Consensus Agent ---
            if agent_signals:
                consensus_payload = {
                    "ticker": asset.ticker,
                    "signals": agent_signals
                }
                try:
                    res = call_agent(f"{AGENTS['consensus']}/decide", consensus_payload)
                    logger.info(f">>> FINAL DECISION for {asset.ticker}: {res['final_signal']} (Conf: {res['confidence_score']})")
                    save_output(db, asset.id, "consensus_agent", res['final_signal'], res['confidence_score'], res)
                except Exception as e:
                     logger.error(f"Consensus Agent failed for {asset.ticker}: {e}")
        
    finally:
        db.close()

def save_output(db, asset_id, agent, signal, score, details):
    out = AgentOutput(
        asset_id=asset_id,
        agent_name=agent,
        signal=str(signal),
        score=float(score) if score else 0.0,
        details=json.dumps(details),
        generated_at=datetime.utcnow()
    )
    db.add(out)
    db.commit()

if __name__ == "__main__":
    run_pipeline()
