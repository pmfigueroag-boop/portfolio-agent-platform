import requests
import json
import os
from sqlalchemy.orm import Session
from datetime import datetime
from services.shared.database import SessionLocal
from services.shared.models.domain import Asset, Price, Fundamental, MacroData, AgentOutput, FinalDecision
from services.shared.logger import setup_logger
from services.shared.models.enums import SignalType
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import hashlib
from services.shared.config import settings
from services.shared.mode_engine import ModeMachine

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
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": settings.API_KEY_SECRET
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()

def calculate_hash(prev_hash: str, data: str) -> str:
    """Creates a SHA-256 hash chain."""
    return hashlib.sha256(f"{prev_hash}{data}".encode()).hexdigest()

def run_pipeline():
    logger.info("Starting Pipeline Execution...")
    
    # Mode Check
    mm = ModeMachine()
    if not mm.is_safe_to_execute():
        logger.critical(f"System Mode is {mm.get_mode()}. Aborting execution.")
        return

    db = SessionLocal()
    try:
        run_id = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
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
        
        logger.info(f"--- Calling Macro Agent ---")
        macro_signal = "NEUTRAL"
        try:
            start_time = datetime.now()
            macro_resp = call_agent(f"{AGENTS['macro']}/analyze", macro_payload)
            latency = (datetime.now() - start_time).total_seconds()
            macro_signal = macro_resp.get('signal', 'NEUTRAL')
            logger.info(f"Macro Agent: Signal={macro_signal} | Latency={latency:.3f}s")
        except Exception as e:
            logger.error(f"Macro Agent failed: {e}")
            macro_signal = "NEUTRAL"

        # 2. Iterate Assets
        pipeline_results = []
        assets = db.query(Asset).all()
        for asset in assets:
            logger.info(f"Processing Asset: {asset.ticker}")
            
            # Fetch Context Data
            prices = db.query(Price).filter(Price.asset_id == asset.id).order_by(Price.date.asc()).all()
            fundamental = db.query(Fundamental).filter(Fundamental.asset_id == asset.id).order_by(Fundamental.reporting_date.desc()).first()
            
            # Log Data Availability
            price_count = len(prices)
            has_fundamental = bool(fundamental)
            logger.info(f"Data Check for {asset.ticker}: Prices={price_count} | Fundamentals={has_fundamental}")

            if not prices or len(prices) < 30:
                logger.warning(f"Skipping {asset.ticker}: Insufficient price data ({price_count} rows)")
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
                    start_time = datetime.now()
                    res = call_agent(f"{AGENTS['value']}/analyze", value_payload)
                    latency = (datetime.now() - start_time).total_seconds()
                    
                    sig = res.get('signal', 'HOLD')
                    logger.info(f"Value Agent [{asset.ticker}]: Signal={sig} | Latency={latency:.3f}s")
                    
                    agent_signals.append({
                        "agent_name": "Value",
                        "signal": sig,
                        "weight": 1.0,
                        "score": 0.0
                    })
                    save_output(db, asset.id, "value_agent", sig, 0.0, res, run_id)
                except Exception as e:
                    logger.error(f"Value Agent failed for {asset.ticker}: {e}")
            else:
                logger.warning(f"Value Agent skipped for {asset.ticker}: No fundamental data")

            # --- Quant Agent ---
            quant_payload = {"ticker": asset.ticker, "prices": price_list}
            try:
                start_time = datetime.now()
                res = call_agent(f"{AGENTS['quant']}/analyze", quant_payload)
                latency = (datetime.now() - start_time).total_seconds()
                
                sig = res.get('signal', 'HOLD')
                score = res.get('momentum_score', 0.0)
                logger.info(f"Quant Agent [{asset.ticker}]: Signal={sig} | Score={score:.2f} | Latency={latency:.3f}s")
                
                agent_signals.append({
                    "agent_name": "Quant",
                    "signal": sig,
                    "weight": 1.0,
                    "score": score
                })
                save_output(db, asset.id, "quant_agent", sig, score, res, run_id)
            except Exception as e:
                 logger.error(f"Quant Agent failed for {asset.ticker}: {e}")

            # --- Risk Agent ---
            risk_payload = {"prices": price_list, "target_volatility": 0.15}
            try:
                start_time = datetime.now()
                res = call_agent(f"{AGENTS['risk']}/analyze", risk_payload)
                latency = (datetime.now() - start_time).total_seconds()
                
                exposure = res.get('risk_adjusted_exposure', 0.5)
                risk_sig = SignalType.HOLD
                if exposure < 0.5:
                    risk_sig = SignalType.SELL
                elif exposure >= 0.9:
                    risk_sig = SignalType.BUY
                
                logger.info(f"Risk Agent [{asset.ticker}]: Exposure={exposure:.2f} | Signal={risk_sig} | Latency={latency:.3f}s")
                
                agent_signals.append({
                    "agent_name": "Risk",
                    "signal": risk_sig, 
                    "weight": 1.5,
                    "score": exposure
                })
                save_output(db, asset.id, "risk_agent", str(risk_sig), exposure, res, run_id)
            except Exception as e:
                 logger.error(f"Risk Agent failed for {asset.ticker}: {e}")
            
            # --- Include Macro Signal ---
            # Always include Macro if available
            agent_signals.append({
                 "agent_name": "Macro",
                 "signal": macro_signal,
                 "weight": 0.5,
                 "score": 0.0
            })

            # --- Consensus Decision ---
            if agent_signals:
                consensus_payload = {
                    "ticker": asset.ticker,
                    "signals": agent_signals
                }
                try:
                    start_time = datetime.now()
                    res = call_agent(f"{AGENTS['consensus']}/decide", consensus_payload)
                    latency = (datetime.now() - start_time).total_seconds()
                    
                    final_sig = res.get('final_signal', 'HOLD')
                    conf_score = res.get('confidence_score', 0.0)
                    
                    logger.info(f">>> CONSENSUS for {asset.ticker}: {final_sig} (Conf: {conf_score:.2f}) | Signals={len(agent_signals)} | Latency={latency:.3f}s")
                    
                    save_output(db, asset.id, "consensus_agent", final_sig, conf_score, res, run_id)
                    
                    # Store Final Decision with Hash Chain
                    last_decision = db.query(FinalDecision).order_by(FinalDecision.id.desc()).first()
                    prev_hash = last_decision.hash if last_decision and last_decision.hash else "0" * 64
                    
                    details_json = json.dumps(res)
                    current_hash = calculate_hash(prev_hash, f"{asset.ticker}{final_sig}{conf_score}{details_json}")

                    final = FinalDecision(
                        ticker=asset.ticker,
                        decision=final_sig,
                        confidence=conf_score,
                        details=details_json,
                        hash=current_hash,
                        previous_hash=prev_hash,
                        run_id=run_id,
                        created_at=datetime.utcnow()
                    )
                    db.add(final)
                    db.commit()
                    
                    flat_result = {
                        "ticker": asset.ticker,
                        "decision": final_sig,
                        "confidence": float(conf_score),
                        "raw_score": float(res.get('details', {}).get('raw_score', 0.0)),
                        "agents_count": len(agent_signals),
                    }
                    pipeline_results.append(flat_result)

                except Exception as e:
                     logger.error(f"Consensus Agent failed for {asset.ticker}: {e}")
            else:
                logger.warning(f"NO SIGNALS collected for {asset.ticker}. Marking as NO_SIGNAL.")
                # Handle NO_SIGNAL case
                flat_result = {
                    "ticker": asset.ticker,
                    "decision": "NO_SIGNAL",
                    "confidence": 0.0,
                    "raw_score": 0.0,
                    "agents_count": 0
                }
                pipeline_results.append(flat_result)
        
        # 3. Upload Results to MinIO
        if pipeline_results:
            run_id = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            final_payload = {
                "run_id": run_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "results": pipeline_results
            }
            upload_to_minio(final_payload, run_id)
        
    finally:
        db.close()

def save_output(db, asset_id, agent, signal, score, details, run_id):
    # Fetch last output for this agent to chain
    last_output = db.query(AgentOutput).filter(AgentOutput.agent_name == agent).order_by(AgentOutput.id.desc()).first()
    prev_hash = last_output.hash if last_output and last_output.hash else "0" * 64
    
    details_str = json.dumps(details)
    current_hash = calculate_hash(prev_hash, f"{asset_id}{agent}{signal}{score}{details_str}")

    out = AgentOutput(
        asset_id=asset_id,
        agent_name=agent,
        signal=str(signal),
        score=float(score) if score else 0.0,
        details=details_str,
        hash=current_hash,
        previous_hash=prev_hash,
        run_id=run_id,
        generated_at=datetime.utcnow()
    )
    db.add(out)
    db.commit()

def upload_to_minio(data, run_id):
    try:
        import boto3
        from botocore.exceptions import ClientError
        from services.shared.config import settings
    except Exception as e:
        logger.error(f"Failed to import boto3: {e}")
        return

    s3_client = boto3.client(
        's3',
        endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        config=boto3.session.Config(signature_version='s3v4'),
        verify=False
    )
    
    bucket_name = "portfolio-results"
    try:
        if bucket_name not in [b['Name'] for b in s3_client.list_buckets()['Buckets']]:
            s3_client.create_bucket(Bucket=bucket_name)
        
        # Governance: Enable Versioning
        s3_client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
    except Exception as e:
        logger.warning(f"Could not check/create bucket or enable versioning: {e}")

    filename = f"run_{run_id}.json"
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=json.dumps(data, indent=2),
            ContentType='application/json'
        )
        logger.info(f"Successfully uploaded results to MinIO: {bucket_name}/{filename}")
    except Exception as e:
        logger.error(f"Failed to upload to MinIO: {e}")

if __name__ == "__main__":
    run_pipeline()
