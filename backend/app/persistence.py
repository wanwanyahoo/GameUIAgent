from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


STORE_SECTIONS = [
    "users",
    "tokens",
    "projects",
    "assets",
    "audit_events",
    "jobs",
    "ai_job_queue",
    "inference_runs",
    "irs",
    "exports",
    "snapshots",
    "imports",
    "api_keys",
    "webhooks",
    "webhook_deliveries",
    "developer_tasks",
    "import_logs",
    "plugin_devices",
    "billing_accounts",
    "usage_events",
    "rate_limits",
    "studio_states",
    "teams",
    "memberships",
    "password_reset_tokens",
    "email_deliveries",
    "asset_versions",
]


class PersistentSection(dict[str, Any]):
    def __init__(self, name: str, parent: "ProductionStore", initial: dict[str, Any] | None = None) -> None:
        super().__init__(initial or {})
        self.name = name
        self.parent = parent

    def __setitem__(self, key: str, value: Any) -> None:
        super().__setitem__(key, value)
        self.parent.flush()

    def __delitem__(self, key: str) -> None:
        super().__delitem__(key)
        self.parent.flush()

    def clear(self) -> None:
        super().clear()
        self.parent.flush()

    def pop(self, key: str, default: Any = None) -> Any:
        value = super().pop(key, default)
        self.parent.flush()
        return value

    def setdefault(self, key: str, default: Any = None) -> Any:
        if key not in self:
            super().__setitem__(key, default)
            self.parent.flush()
        return self[key]

    def update(self, *args: Any, **kwargs: Any) -> None:
        super().update(*args, **kwargs)
        self.parent.flush()


class ProductionStore(dict[str, PersistentSection]):
    def __init__(self) -> None:
        super().__init__({section: PersistentSection(section, self) for section in STORE_SECTIONS})
        self.db_path: str | None = None
        self._loading = False

    def configure(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS store_sections ("
                "section TEXT PRIMARY KEY, "
                "payload TEXT NOT NULL)"
            )
        self.reload()

    def reload(self) -> None:
        if not self.db_path:
            return
        self._loading = True
        try:
            with sqlite3.connect(self.db_path) as connection:
                rows = dict(connection.execute("SELECT section, payload FROM store_sections").fetchall())
            for section in STORE_SECTIONS:
                payload = json.loads(rows.get(section, "{}"))
                dict.__setitem__(self, section, PersistentSection(section, self, payload))
        finally:
            self._loading = False

    def flush(self) -> None:
        if not self.db_path or self._loading:
            return
        with sqlite3.connect(self.db_path) as connection:
            connection.executemany(
                "INSERT INTO store_sections(section, payload) VALUES (?, ?) "
                "ON CONFLICT(section) DO UPDATE SET payload = excluded.payload",
                [
                    (section, json.dumps(dict(self[section]), sort_keys=True))
                    for section in STORE_SECTIONS
                ],
            )


def create_production_store() -> ProductionStore:
    return ProductionStore()
