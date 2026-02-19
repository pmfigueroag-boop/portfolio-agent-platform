from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from services.shared.models.base import Base

class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    sector = Column(String)
    industry = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    prices = relationship("Price", back_populates="asset")
    fundamentals = relationship("Fundamental", back_populates="asset")

class Price(Base):
    __tablename__ = "prices"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    adjusted_close = Column(Float)
    
    asset = relationship("Asset", back_populates="prices")
    
    __table_args__ = (
        Index('idx_price_asset_date', 'asset_id', 'date', unique=True),
    )

class Fundamental(Base):
    __tablename__ = "fundamentals"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    reporting_date = Column(DateTime, nullable=False)
    period = Column(String, nullable=False) # Q1, Q2, FY2023, etc.
    
    # Value Agent Metrics
    roe = Column(Float)
    fcf = Column(Float)
    debt_to_ebitda = Column(Float)
    intrinsic_value = Column(Float)
    
    asset = relationship("Asset", back_populates="fundamentals")

class MacroData(Base):
    __tablename__ = "macro_data"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, unique=True)
    inflation_rate = Column(Float)
    interest_rate = Column(Float)
    gdp_growth = Column(Float)
    unemployment_rate = Column(Float)

class AgentOutput(Base):
    __tablename__ = "agent_outputs"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    agent_name = Column(String, nullable=False) # "value_agent", "quant_agent"
    signal = Column(String, nullable=False) # "buy", "sell", "hold"
    score = Column(Float) # 0.0 to 1.0
    details = Column(String)
    hash = Column(String)
    previous_hash = Column(String)
    run_id = Column(String, index=True)
    generated_at = Column(DateTime, default=datetime.utcnow)

class FinalDecision(Base):
    __tablename__ = "final_decisions"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, nullable=False)
    decision = Column(String, nullable=False) # BUY, SELL, HOLD
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    details = Column(String)
    hash = Column(String)
    previous_hash = Column(String)
    run_id = Column(String, index=True)
