from __future__ import annotations

from pathlib import Path
from uuid import uuid4


class LocalStorage:
    def __init__(self, root: Path) -> None:
        self.root = root.expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, object_key: str) -> Path:
        candidate = Path(object_key)
        if candidate.is_absolute() or not candidate.parts:
            raise ValueError("INVALID_OBJECT_KEY")
        resolved = (self.root / candidate).resolve()
        if self.root not in resolved.parents:
            raise ValueError("INVALID_OBJECT_KEY")
        if candidate.parts[0] not in {"private", "public"}:
            raise ValueError("INVALID_OBJECT_KEY")
        return resolved

    def save(self, data: bytes, *, namespace: str, suffix: str) -> str:
        if namespace not in {"private", "public"}:
            raise ValueError("INVALID_NAMESPACE")
        extension = suffix.casefold().lstrip(".")
        if extension not in {"jpg", "jpeg", "png", "webp"}:
            raise ValueError("INVALID_SUFFIX")
        object_key = f"{namespace}/{uuid4().hex}.{extension}"
        path = self._path_for(object_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return object_key

    def read(self, object_key: str) -> bytes:
        return self._path_for(object_key).read_bytes()

    def delete(self, object_key: str) -> None:
        path = self._path_for(object_key)
        if path.exists():
            path.unlink()

    def path_for(self, object_key: str) -> Path:
        return self._path_for(object_key)
