"""Create tables for local development.

Usage (from services/core-api):  python -m scripts.create_tables

Replace this with Alembic migrations once migration tooling is set up.
"""

from app.db.base import Base
from app.db.session import engine
from app.modules.resumes import models  # noqa: F401  (registers tables on Base.metadata)


def main() -> None:
    Base.metadata.create_all(engine)
    print("Tables created:", ", ".join(sorted(Base.metadata.tables)))


if __name__ == "__main__":
    main()
