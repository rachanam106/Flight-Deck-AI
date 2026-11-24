
from pathlib import Path

import sqlparse
from sqlalchemy import text

from app.core.database import engine


def create_schema():
    schema_path = (
        Path(__file__).resolve().parents[1]
        / "database"
        / "schema.sql"
    )

    schema_sql = schema_path.read_text(encoding="utf-8")

    # Split SQL correctly and remove comments.
    statements = [
        statement.strip()
        for statement in sqlparse.split(schema_sql)
        if statement.strip()
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))

    print("Flight Deck database schema created successfully.")
    print(f"Executed {len(statements)} SQL statements.")


if __name__ == "__main__":
    create_schema()
