import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from services.shared.database import SessionLocal, engine, Base
from services.shared.models.domain import Asset, Price, Fundamental, MacroData
from services.shared.logger import setup_logger

logger = setup_logger("seeder")

def seed_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Clear existing data (optional, for dev)
        # db.query(Price).delete()
        # db.query(Fundamental).delete()
        # db.query(Asset).delete()
        # db.query(MacroData).delete()
        # db.commit()
        
        # 2. Seed Assets
        assets = [
            {"ticker": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
            {"ticker": "MSFT", "name": "Microsoft Corp.", "sector": "Technology"},
            {"ticker": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
            {"ticker": "JPM", "name": "JPMorgan Chase", "sector": "Finance"},
            {"ticker": "XOM", "name": "Exxon Mobil", "sector": "Energy"},
            {"ticker": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Cyclical"},
            {"ticker": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare"},
            {"ticker": "V", "name": "Visa Inc.", "sector": "Finance"},
            {"ticker": "WMT", "name": "Walmart Inc.", "sector": "Consumer Defensive"},
            {"ticker": "PG", "name": "Procter & Gamble", "sector": "Consumer Defensive"},
        ]
        
        created_assets = []
        for a in assets:
            existing = db.query(Asset).filter(Asset.ticker == a["ticker"]).first()
            if not existing:
                asset = Asset(**a)
                db.add(asset)
                db.commit()
                db.refresh(asset)
                created_assets.append(asset)
                logger.info(f"Created asset: {asset.ticker}")
            else:
                created_assets.append(existing)
        
        # 3. Seed Prices (last 200 days)
        for asset in created_assets:
            # Check if prices exist
            if db.query(Price).filter(Price.asset_id == asset.id).count() > 0:
                continue
                
            price = 150.0 # Start price
            date = datetime.now() - timedelta(days=200)
            
            for i in range(200):
                date += timedelta(days=1)
                # Random walk
                change = random.uniform(-0.02, 0.02)
                price *= (1 + change)
                
                p = Price(
                    asset_id=asset.id,
                    date=date,
                    open=price * 0.99,
                    high=price * 1.02,
                    low=price * 0.98,
                    close=price,
                    volume=random.randint(1000000, 5000000),
                    adjusted_close=price
                )
                db.add(p)
            db.commit()
            logger.info(f"Seeded prices for {asset.ticker}")
            
        # 4. Seed Fundamentals
        for asset in created_assets:
            if db.query(Fundamental).filter(Fundamental.asset_id == asset.id).count() > 0:
                continue
                
            f = Fundamental(
                asset_id=asset.id,
                reporting_date=datetime.now(),
                period="FY2025",
                roe=random.uniform(0.10, 0.35),
                fcf=random.uniform(1e9, 5e9),
                debt_to_ebitda=random.uniform(0.5, 4.0),
                intrinsic_value=random.uniform(100, 200) # Dummy
            )
            # Add EBITDA/Debt explicitly if model supports, stored in generic/computed fields usually
            # But here we used robust models, let's fix Fundamental model to match schema logic?
            # Wait, our Fundamental model has roe, fcf, debt_to_ebitda. 
            # The API input needs Debt and EBITDA separate.
            # We should probably store those in Fundamental to be useful.
            # Checking `services/shared/models/domain.py`: 
            # roe, fcf, debt_to_ebitda, intrinsic_value.
            # It lacks raw debt/ebitda. I will add them to the model now or just mock them in pipeline.
            # For strictness, I should update the model. But purely for seeding what exists:
            db.add(f)
            db.commit()
            logger.info(f"Seeded fundamentals for {asset.ticker}")

        # 5. Seed Macro Data
        if db.query(MacroData).count() == 0:
             m = MacroData(
                 date=datetime.now(),
                 inflation_rate=0.035,
                 interest_rate=0.0525,
                 gdp_growth=0.021,
                 unemployment_rate=0.039
             )
             db.add(m)
             db.commit()
             logger.info("Seeded macro data")
             
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
