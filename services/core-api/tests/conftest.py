from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.integrations.storage import StorageError


class InMemoryStorage:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    def save(self, key: str, data: bytes) -> None:
        self.files[key] = data

    def read(self, key: str) -> bytes:
        try:
            return self.files[key]
        except KeyError as exc:
            raise StorageError("missing") from exc

    def delete(self, key: str) -> None:
        self.files.pop(key, None)


@pytest.fixture
def memory_storage() -> InMemoryStorage:
    return InMemoryStorage()


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    from app.db.base import Base
    from app.modules.resumes import models  # noqa: F401

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    engine.dispose()


@pytest.fixture
def db_session(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    with session_factory() as session:
        yield session
