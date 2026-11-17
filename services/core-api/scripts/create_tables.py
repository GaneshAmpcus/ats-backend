"""Create tables for local development.

Usage (from services/core-api):  python -m scripts.create_tables

Replace this with Alembic migrations once migration tooling is set up.
"""

from app.db.base import Base
from sqlalchemy import text
from app.db.session import engine
from app.modules.resumes import models  # noqa: F401  (registers tables on Base.metadata)


def main() -> None:
    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)
    print("Tables created:", ", ".join(sorted(Base.metadata.tables)))


if __name__ == "__main__":
    main()
