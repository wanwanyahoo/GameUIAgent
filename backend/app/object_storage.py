from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from re import sub
from uuid import uuid4


@dataclass(frozen=True)
class StoredObject:
    key: str
    path: Path
    size_bytes: int
    sha256: str
    content_type: str


class LocalObjectStorage:
    def __init__(self) -> None:
        self.root: Path | None = None

    def configure(self, root_path: str) -> None:
        self.root = Path(root_path)
        self.root.mkdir(parents=True, exist_ok=True)

    @property
    def durable(self) -> bool:
        return self.root is not None

    def put(self, project_id: str, filename: str, content: bytes, content_type: str) -> StoredObject:
        if not self.root:
            raise RuntimeError("Object storage is not configured")
        safe_name = sub(r"[^a-zA-Z0-9._-]+", "-", filename).strip("-") or "asset.bin"
        key = f"{project_id}/{uuid4().hex}-{safe_name}"
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return StoredObject(
            key=key,
            path=path,
            size_bytes=len(content),
            sha256=sha256(content).hexdigest(),
            content_type=content_type,
        )

    def path_for(self, key: str) -> Path:
        if not self.root:
            raise RuntimeError("Object storage is not configured")
        path = (self.root / key).resolve()
        root = self.root.resolve()
        if root not in path.parents and path != root:
            raise ValueError("Object key escapes storage root")
        return path


def create_object_storage() -> LocalObjectStorage:
    return LocalObjectStorage()
