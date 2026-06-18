"""Content backlog and per-day pipeline-item state, persisted as JSON."""
from __future__ import annotations

import json
import uuid
from pathlib import Path


# ---------- backlog ----------

def add_topic(backlog: list[dict], title: str, notes: str = "") -> dict:
    item = {"id": uuid.uuid4().hex, "title": title, "notes": notes,
            "status": "proposed"}
    backlog.append(item)
    return item


def promote_topic(backlog: list[dict], topic_id: str) -> dict:
    for item in backlog:
        if item["id"] == topic_id:
            item["status"] = "ready"
            return item
    raise KeyError(topic_id)


def next_ready_topic(backlog: list[dict]) -> dict | None:
    for item in backlog:
        if item["status"] == "ready":
            return item
    return None


def count_ready(backlog: list[dict]) -> int:
    return sum(1 for item in backlog if item["status"] == "ready")


def _backlog_path(data_dir: Path | str) -> Path:
    return Path(data_dir) / "backlog.json"


def load_backlog(data_dir: Path | str) -> list[dict]:
    path = _backlog_path(data_dir)
    if not path.exists():
        return []
    return json.loads(path.read_text())


def save_backlog(data_dir: Path | str, backlog: list[dict]) -> None:
    path = _backlog_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(backlog, indent=2))
