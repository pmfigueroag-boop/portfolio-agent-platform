import sys
import hashlib
import json
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from services.shared.config import settings
from services.shared.models.domain import AgentOutput, FinalDecision

def calculate_hash(prev_hash: str, data: str) -> str:
    """Replicates the SHA-256 hash chain logic from pipeline.py"""
    return hashlib.sha256(f"{prev_hash}{data}".encode()).hexdigest()

def verify_agent_outputs(session):
    print("\n--- Verifying Agent Outputs (Per Agent Chain) ---")
    agents = session.query(AgentOutput.agent_name).distinct().all()
    agent_names = [a[0] for a in agents]
    
    all_valid = True
    
    for agent in agent_names:
        print(f"Checking chain for agent: {agent}")
        outputs = session.query(AgentOutput).filter(AgentOutput.agent_name == agent).order_by(AgentOutput.id.asc()).all()
        
        expected_prev = "0" * 64
        for out in outputs:
            # Reconstruct data string
            # pipeline.py: f"{asset_id}{agent}{signal}{score}{details_str}"
            # Note: score is float, conversion to string must match exactly what Python did in pipeline
            # Ideally pipeline should use f"{float(score)}" but it likely used default str(float). 
            # We need to match the production logic exactly.
            
            # pipeline.py logic:
            # score=float(score) if score else 0.0
            # f"{asset_id}{agent}{signal}{score}{details_str}"
            
            # Warning: Python's float to string representation can vary. 
            # In pipeline.py: f"{...}{score}{...}" uses standard formatting.
            
            data_str = f"{out.asset_id}{out.agent_name}{out.signal}{out.score}{out.details}"
            calculated_hash = calculate_hash(expected_prev, data_str)
            
            if out.previous_hash != expected_prev:
                print(f"  [BROKEN CHAIN] ID {out.id}: Previous hash mismatch!")
                print(f"    Expected Prev: {expected_prev}")
                print(f"    Actual Prev:   {out.previous_hash}")
                all_valid = False
                break
            
            if out.hash != calculated_hash:
                print(f"  [TAMPER DETECTED] ID {out.id}: Hash mismatch!")
                print(f"    Data: {data_str}")
                print(f"    Calculated: {calculated_hash}")
                print(f"    Stored:     {out.hash}")
                all_valid = False
                break
            
            expected_prev = out.hash
            
    if all_valid:
        print("✅ Agent Output Chains: VALID")
    else:
        print("❌ Agent Output Chains: INVALID")

def verify_final_decisions(session):
    print("\n--- Verifying Final Decisions (Global Chain) ---")
    decisions = session.query(FinalDecision).order_by(FinalDecision.id.asc()).all()
    
    all_valid = True
    expected_prev = "0" * 64
    
    for dec in decisions:
        # pipeline.py: f"{asset.ticker}{final_sig}{conf_score}{details_json}"
        data_str = f"{dec.ticker}{dec.decision}{dec.confidence}{dec.details}"
        calculated_hash = calculate_hash(expected_prev, data_str)
        
        if dec.previous_hash != expected_prev:
            print(f"  [BROKEN CHAIN] ID {dec.id}: Previous hash mismatch!")
            all_valid = False
            break
            
        if dec.hash != calculated_hash:
            print(f"  [TAMPER DETECTED] ID {dec.id}: Hash mismatch!")
            print(f"    Data: {data_str}")
            print(f"    Calculated: {calculated_hash}")
            print(f"    Stored:     {dec.hash}")
            all_valid = False
            break
            
        expected_prev = dec.hash

    if all_valid:
        print("✅ Final Decision Chain: VALID")
    else:
        print("❌ Final Decision Chain: INVALID")

if __name__ == "__main__":
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        verify_agent_outputs(session)
        verify_final_decisions(session)
    except Exception as e:
        print(f"Verification Failed: {e}")
    finally:
        session.close()
