from services.shared.database import engine
from services.shared.models.base import Base
from services.shared.models import domain # Import to register models

print("Creating all tables...")
Base.metadata.create_all(bind=engine)
print("Tables created.")
