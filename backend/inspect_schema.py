
from sqlalchemy import text
from app.core.database import engine

query = text("""
    SELECT
        table_name,
        column_name,
        data_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
    ORDER BY table_name, ordinal_position
""")

with engine.connect() as connection:
    rows = connection.execute(query).mappings().all()

current_table = None

print("\nFLIGHT DECK DATABASE SCHEMA")
print("=" * 55)

for row in rows:
    if row["table_name"] != current_table:
        current_table = row["table_name"]
        print(f"\n{current_table}")
        print("-" * 35)

    print(f"  {row['column_name']:<30} {row['data_type']}")
