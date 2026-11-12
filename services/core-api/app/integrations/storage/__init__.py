from app.core.config import get_settings
from app.integrations.storage.base import FileStorage, StorageError
from app.integrations.storage.local import LocalFileStorage

__all__ = ["FileStorage", "LocalFileStorage", "StorageError", "get_resume_storage"]


def get_resume_storage() -> FileStorage:
    """Return the storage backend used for uploaded resumes."""
    return LocalFileStorage(get_settings().resume_storage_dir)
