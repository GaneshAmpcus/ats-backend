from typing import Protocol


class StorageError(Exception):
    """Raised when a file cannot be written to, read from, or removed from storage."""


class FileStorage(Protocol):
    """Minimal storage interface. Implement it for S3/GCS/Azure to replace local disk."""

    def save(self, key: str, data: bytes) -> None: ...

    def read(self, key: str) -> bytes: ...

    def delete(self, key: str) -> None: ...
