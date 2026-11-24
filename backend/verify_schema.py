
from sqlalchemy import text
from app.core.database import engine

query = text("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_type = 'BASE TABLE'
    ORDER BY table_name
""")

with engine.connect() as connection:
    tables = connection.execute(query).scalars().all()

print("\nFlight Deck database tables:")
for table in tables:
    print(f"  [OK] {table}")

print(f"\nTotal tables found: {len(tables)}")

