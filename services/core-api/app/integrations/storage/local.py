from pathlib import Path

from app.integrations.storage.base import StorageError


class LocalFileStorage:
    """Stores files on local disk under a fixed root directory."""

    def __init__(self, root: Path) -> None:
        self._root = Path(root).resolve()

    def _resolve(self, key: str) -> Path:
        path = (self._root / key).resolve()
        if path == self._root or self._root not in path.parents:
            raise StorageError("Invalid storage key.")
        return path

    def save(self, key: str, data: bytes) -> None:
        path = self._resolve(key)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = path.with_name(path.name + ".tmp")
            temp_path.write_bytes(data)
            temp_path.replace(path)
        except OSError as exc:
            raise StorageError("Failed to write file to storage.") from exc

    def read(self, key: str) -> bytes:
        path = self._resolve(key)
        try:
            return path.read_bytes()
        except OSError as exc:
            raise StorageError("Failed to read file from storage.") from exc

    def delete(self, key: str) -> None:
        path = self._resolve(key)
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise StorageError("Failed to delete file from storage.") from exc
