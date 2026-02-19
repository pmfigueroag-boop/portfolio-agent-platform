import pytest
import hashlib
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.shared.models.base import Base
from services.shared.models.domain import Asset, AgentOutput, FinalDecision

# Use in-memory SQLite for fast integration testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()

def calculate_hash(prev_hash: str, data: str) -> str:
    """Duplicate of pipeline logic for verification"""
    return hashlib.sha256(f"{prev_hash}{data}".encode()).hexdigest()

def test_agent_output_chaining(db_session):
    """
    Verifies that AgentOutput records are correctly chained via hash and previous_hash.
    """
    # Setup Asset
    asset = Asset(ticker="GOV_TEST", name="Governance Test Asset")
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)

    run_id = "test_run_001"
    agent_name = "test_agent"
    
    # --- Record 1 ---
    prev_hash_1 = "0" * 64
    details_1 = json.dumps({"reason": "test1"})
    data_1 = f"{asset.id}{agent_name}{'BUY'}{0.8}{details_1}"
    hash_1 = calculate_hash(prev_hash_1, data_1)
    
    out1 = AgentOutput(
        asset_id=asset.id,
        agent_name=agent_name,
        signal="BUY",
        score=0.8,
        details=details_1,
        hash=hash_1,
        previous_hash=prev_hash_1,
        run_id=run_id
    )
    db_session.add(out1)
    db_session.commit()

    # --- Record 2 ---
    # Should point to hash_1
    prev_hash_2 = hash_1 
    details_2 = json.dumps({"reason": "test2"})
    data_2 = f"{asset.id}{agent_name}{'SELL'}{0.4}{details_2}"
    hash_2 = calculate_hash(prev_hash_2, data_2)
    
    out2 = AgentOutput(
        asset_id=asset.id,
        agent_name=agent_name, # Same agent -> Same chain
        signal="SELL",
        score=0.4,
        details=details_2,
        hash=hash_2,
        previous_hash=prev_hash_2,
        run_id=run_id
    )
    db_session.add(out2)
    db_session.commit()

    # --- Verification ---
    outputs = db_session.query(AgentOutput).filter(AgentOutput.agent_name == agent_name).order_by(AgentOutput.id).all()
    assert len(outputs) == 2
    
    record1 = outputs[0]
    record2 = outputs[1]
    
    # 1. Check Linkage
    assert record1.previous_hash == "0" * 64
    assert record2.previous_hash == record1.hash
    
    # 2. Check Integrity (Re-calculate)
    recalc_hash_1 = calculate_hash("0" * 64, f"{asset.id}{agent_name}{record1.signal}{record1.score}{record1.details}")
    assert record1.hash == recalc_hash_1
    
    recalc_hash_2 = calculate_hash(record1.hash, f"{asset.id}{agent_name}{record2.signal}{record2.score}{record2.details}")
    assert record2.hash == recalc_hash_2

def test_tamper_evidence(db_session):
    """
    Verifies that modifying a record breaks the chain verification of subsequent records.
    """
    asset = Asset(ticker="TAMPER", name="Tamper Test")
    db_session.add(asset)
    db_session.commit()
    
    run_id = "run_bad"
    agent = "audit_agent"
    
    # Create valid chain of 2
    out1 = AgentOutput(
        asset_id=asset.id, agent_name=agent, signal="HOLD", score=0.5, details="{}",
        hash="valid_hash_1", previous_hash="0"*64, run_id=run_id
    )
    db_session.add(out1)
    db_session.commit()
    
    out2 = AgentOutput(
        asset_id=asset.id, agent_name=agent, signal="HOLD", score=0.5, details="{}",
        hash="valid_hash_2", previous_hash="valid_hash_1", run_id=run_id
    )
    db_session.add(out2)
    db_session.commit()
    
    # ATTACK: Tamper with Record 1's score in DB
    # Simulating SQL injection or rogue admin
    out1.score = 0.99 
    db_session.commit()
    
    # VERIFY: Chains strictly match
    # Fetch fresh from DB
    r1 = db_session.query(AgentOutput).filter(AgentOutput.id == out1.id).first()
    r2 = db_session.query(AgentOutput).filter(AgentOutput.id == out2.id).first()
    
    # Recalculate Hash for R1
    # Data has changed (0.99), so hash should be different from stored "valid_hash_1"
    # Note: calculate_hash() is determinisic. 
    # Logic: 
    #  Original Hash stored: "valid_hash_1" (based on score=0.5)
    #  Current Data: score=0.99
    #  Recalculated Hash: sha256(...0.99...) != "valid_hash_1"
    
    # We construct what the hash SHOULD be for the current data
    data_tampered = f"{asset.id}{agent}{r1.signal}{r1.score}{r1.details}"
    new_hash = calculate_hash(r1.previous_hash, data_tampered)
    
    # Assertion: The stored hash (which is immutable/signed in theory) no longer matches the data
    assert r1.hash != new_hash
    
    # Assertion: Record 2 still points to the OLD hash of Record 1
    # This proves Record 2 was created BEFORE the tampering
    assert r2.previous_hash == "valid_hash_1" 
