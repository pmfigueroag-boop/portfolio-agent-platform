"""
Portfolio Agent Platform - Demo Analysis
Runs all 5 agents locally with synthetic AAPL data (no Docker/DB needed).
Optionally persists results to PostgreSQL when Docker DB is available.
Usage: python run_demo.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import hashlib
import json
from datetime import datetime, timedelta, timezone

# Agent imports
from services.value_agent.schema import ValuationInput
from services.value_agent.rules.valuation import calculate_intrinsic_value
from services.quant_agent.schema import QuantInput, PricePoint as QuantPP
from services.quant_agent.rules.signals import calculate_quant_signals
from services.macro_agent.schema import MacroInput
from services.macro_agent.rules.macro_analysis import analyze_macro_regime
from services.risk_agent.schema import RiskInput, PricePoint as RiskPP
from services.risk_agent.rules.risk_metrics import calculate_risk_metrics
from services.consensus_agent.schema import ConsensusInput, AgentSignal
from services.consensus_agent.rules.aggregation import aggregate_signals

def generate_prices(days=252, start=100.0):
    np.random.seed(3)
    prices = [start]
    for _ in range(days - 1):
        prices.append(prices[-1] * (1 + np.random.normal(0.0005, 0.015)))
    return prices

def calculate_hash(prev_hash: str, data: str) -> str:
    return hashlib.sha256(f"{prev_hash}{data}".encode()).hexdigest()

def sep(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")

def persist_to_db(ticker, agent_results, consensus_result, run_id):
    """Persist demo results to PostgreSQL if Docker DB is available."""
    try:
        from sqlalchemy import text
        from services.shared.database import SessionLocal
        from services.shared.models.domain import Asset, AgentOutput, FinalDecision
        db = SessionLocal()
        db.execute(text("SELECT 1"))
    except Exception:
        print("\n  [DB] Docker DB not available - console-only mode")
        return False

    try:
        # Look up (or create) asset
        asset = db.query(Asset).filter(Asset.ticker == ticker).first()
        if not asset:
            asset = Asset(ticker=ticker, name=f"{ticker} Inc.", sector="Technology")
            db.add(asset)
            db.commit()
            db.refresh(asset)
        asset_id = asset.id
        # Persist agent outputs with hash chain
        for agent_name, signal, score, details in agent_results:
            last = db.query(AgentOutput).filter(AgentOutput.agent_name == agent_name).order_by(AgentOutput.id.desc()).first()
            prev_hash = last.hash if last and last.hash else "0" * 64
            details_str = json.dumps(details)
            current_hash = calculate_hash(prev_hash, f"{asset_id}{agent_name}{signal}{score}{details_str}")

            out = AgentOutput(
                asset_id=asset_id,
                agent_name=agent_name,
                signal=signal,
                score=float(score),
                details=details_str,
                hash=current_hash,
                previous_hash=prev_hash,
                run_id=run_id,
                generated_at=datetime.now(timezone.utc)
            )
            db.add(out)
        db.commit()

        # Persist final decision with hash chain
        last_decision = db.query(FinalDecision).order_by(FinalDecision.id.desc()).first()
        prev_hash = last_decision.hash if last_decision and last_decision.hash else "0" * 64
        details_json = json.dumps({
            "raw_score": consensus_result.details['raw_score'],
            "agents_count": consensus_result.details['agents_count']
        })
        current_hash = calculate_hash(prev_hash, f"{ticker}{consensus_result.final_signal.value}{consensus_result.confidence_score}{details_json}")

        final = FinalDecision(
            ticker=ticker,
            decision=consensus_result.final_signal.value,
            confidence=consensus_result.confidence_score,
            details=details_json,
            hash=current_hash,
            previous_hash=prev_hash,
            run_id=run_id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(final)
        db.commit()
        db.close()
        print(f"\n  [DB] Persisted to PostgreSQL | run_id: {run_id} | hash: {current_hash[:16]}...")
        return True
    except Exception as e:
        print(f"\n  [DB] Persistence failed: {e}")
        db.rollback()
        db.close()
        return False

def main():
    TICKER = "AAPL"
    run_id = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    print(f"\nPortfolio Agent Platform - Analisis de Ejemplo: {TICKER}")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    prices = generate_prices(252, 100.0)
    base = datetime.now() - timedelta(days=252)

    # 1. VALUE AGENT
    sep("VALUE AGENT - Analisis Fundamental")
    vr = calculate_intrinsic_value(ValuationInput(
        ticker=TICKER, roe=0.35, fcf=130e9, debt=95e9, ebitda=140e9,
        current_price=prices[-1], shares_outstanding=15.0e9
    ))
    print(f"  Valor Intrinseco:  ${vr.intrinsic_value:,.2f}")
    print(f"  Margen Seguridad:  {vr.margin_of_safety:.0%}")
    print(f"  Signal:            {vr.signal.value}")
    print(f"  Deuda/EBITDA:      {vr.details['debt_to_ebitda']:.2f}x")

    # 2. QUANT AGENT
    sep("QUANT AGENT - Analisis Tecnico & Momentum")
    qp = [QuantPP(date=base + timedelta(days=i), price=prices[i]) for i in range(len(prices))]
    qr = calculate_quant_signals(QuantInput(ticker=TICKER, prices=qp))
    print(f"  Momentum 30d:  {qr.momentum_score:.2%}")
    print(f"  Volatilidad:   {qr.volatility:.2%}")
    print(f"  Signal:        {qr.signal.value}")
    print(f"  MA-50:         ${qr.details['ma_50']:,.2f}")
    print(f"  MA-200:        ${qr.details['ma_200']:,.2f}")

    # 3. MACRO AGENT
    sep("MACRO AGENT - Regimen Macroeconomico")
    mr = analyze_macro_regime(MacroInput(
        inflation_rate=0.025, interest_rate=0.0425, gdp_growth=0.028,
        unemployment_rate=0.041, liquidity_index=0.06
    ))
    print(f"  Regimen:   {mr.regime}")
    print(f"  Signal:    {mr.signal.value}")

    # 4. RISK AGENT
    sep("RISK AGENT - Evaluacion de Riesgo")
    rp = [RiskPP(date=base + timedelta(days=i), price=prices[i]) for i in range(len(prices))]
    rr = calculate_risk_metrics(RiskInput(prices=rp, target_volatility=0.15))
    print(f"  Max Drawdown:       {rr.max_drawdown:.2%}")
    print(f"  Volatilidad Anual:  {rr.volatility:.2%}")
    print(f"  Exposicion Ajust.:  {rr.risk_adjusted_exposure:.0%}")
    print(f"  Drawdown Alert:     {'Si' if rr.details['drawdown_warning'] else 'No'}")
    print(f"  Volatility Alert:   {'Si' if rr.details['volatility_warning'] else 'No'}")

    # 5. CONSENSUS AGENT
    sep("CONSENSUS AGENT - Decision Final")
    cr = aggregate_signals(ConsensusInput(
        ticker=TICKER,
        signals=[
            AgentSignal(agent_name="Value",  signal=vr.signal, weight=1.0),
            AgentSignal(agent_name="Quant",  signal=qr.signal, weight=1.0),
            AgentSignal(agent_name="Macro",  signal=mr.signal, weight=0.5),
            AgentSignal(agent_name="Risk",   signal="HOLD",    weight=0.5),
        ]
    ))
    emoji = {"STRONG_BUY":"++","BUY":"+","HOLD":"=","SELL":"-","STRONG_SELL":"--"}
    print(f"  Decision:   [{emoji.get(cr.final_signal.value,'?')}] {cr.final_signal.value}")
    print(f"  Confianza:  {cr.confidence_score:.0%}")
    print(f"  Score:      {cr.details['raw_score']}")
    print(f"  Agentes:    {int(cr.details['agents_count'])}")

    # SUMMARY
    sep(f"RESUMEN - {TICKER}")
    print(f"  {'Agente':<16} {'Signal':<14} Detalle")
    print(f"  {'-'*16} {'-'*14} {'-'*28}")
    print(f"  {'Value':<16} {vr.signal.value:<14} MoS:{vr.margin_of_safety:.0%} D/E:{vr.details['debt_to_ebitda']:.1f}x")
    print(f"  {'Quant':<16} {qr.signal.value:<14} Mom:{qr.momentum_score:.2%} Vol:{qr.volatility:.2%}")
    print(f"  {'Macro':<16} {mr.signal.value:<14} Regimen:{mr.regime}")
    print(f"  {'Risk':<16} {'N/A':<14} DD:{rr.max_drawdown:.2%} Exp:{rr.risk_adjusted_exposure:.0%}")
    print(f"  {'-'*16} {'-'*14} {'-'*28}")
    print(f"  {'CONSENSUS':<16} {cr.final_signal.value:<14} Confianza:{cr.confidence_score:.0%}")

    # 6. PERSIST TO DB (if Docker is running)
    agent_results = [
        ("value_agent",     vr.signal.value, vr.margin_of_safety, {"intrinsic_value": vr.intrinsic_value, "margin_of_safety": vr.margin_of_safety, "debt_to_ebitda": vr.details['debt_to_ebitda']}),
        ("quant_agent",     qr.signal.value, qr.momentum_score,   {"momentum": qr.momentum_score, "volatility": qr.volatility, "ma_50": qr.details['ma_50'], "ma_200": qr.details['ma_200']}),
        ("macro_agent",     mr.signal.value, 0.0,                  {"regime": mr.regime}),
        ("risk_agent",      "HOLD",          rr.risk_adjusted_exposure, {"max_drawdown": rr.max_drawdown, "volatility": rr.volatility, "exposure": rr.risk_adjusted_exposure}),
        ("consensus_agent", cr.final_signal.value, cr.confidence_score, {"raw_score": cr.details['raw_score'], "agents_count": cr.details['agents_count']}),
    ]
    persist_to_db(TICKER, agent_results, cr, run_id)
    print()

if __name__ == "__main__":
    main()

