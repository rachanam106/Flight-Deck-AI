from sqlalchemy import text
from app.core.database import engine


def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar_one()

        if result == 1:
            print("SUCCESS: Connected to Neon PostgreSQL!")
            print("Test query: SELECT 1")
        else:
            print("FAILED: Unexpected query result.")

    except Exception as error:
        # Do not print connection details or credentials.
        print("FAILED: Could not connect to Neon PostgreSQL.")
        print("Error type:", type(error).__name__)


if __name__ == "__main__":
    test_connection()
