from __future__ import annotations

import json
from pathlib import Path

from app.config.settings import settings


class LocalObjectStorage:
    def put_json(self, storage_key: str, payload: dict) -> str:
        path = Path(settings.local_storage_root) / storage_key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return str(path)
