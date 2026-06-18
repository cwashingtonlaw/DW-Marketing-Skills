"""Content backlog and per-day pipeline-item state, persisted as JSON."""
from __future__ import annotations

import json
import uuid
from datetime import date
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


def consume_next_ready(backlog: list[dict]) -> dict | None:
    for item in backlog:
        if item["status"] == "ready":
            item["status"] = "used"
            return item
    return None


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


# ---------- pipeline item ----------

class InvalidTransition(Exception):
    """Raised when a status change is not allowed."""


ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "generated": {"pending_approval", "hold", "error"},
    "pending_approval": {"approved", "hold"},
    "approved": {"scheduled", "error"},
    "scheduled": {"published", "error"},
    "hold": {"pending_approval", "generated"},
    "error": {"generated"},
    "published": set(),
}


def create_pipeline_item(date: str, topic: dict) -> dict:
    return {
        "date": date,
        "topic_id": topic["id"],
        "title": topic["title"],
        "status": "generated",
        "script_path": None,
        "video_path": None,
        "metadata": {},          # title, description, tags, thumbnail brief
        "compliance_verdict": None,
        "publish_at": None,      # RFC3339 string set at scheduling time
        "publish_date": None,    # local calendar date (YYYY-MM-DD) of the slot
        "youtube_video_id": None,
    }


def set_status(item: dict, new_status: str) -> dict:
    current = item["status"]
    if new_status not in ALLOWED_TRANSITIONS.get(current, set()):
        raise InvalidTransition(f"{current} -> {new_status}")
    item["status"] = new_status
    return item


def _pipeline_dir(data_dir: Path | str, date: str) -> Path:
    return Path(data_dir) / "pipeline" / date


def save_pipeline_item(data_dir: Path | str, item: dict) -> None:
    d = _pipeline_dir(data_dir, item["date"])
    d.mkdir(parents=True, exist_ok=True)
    (d / "metadata.json").write_text(json.dumps(item, indent=2))


def load_pipeline_item(data_dir: Path | str, date: str) -> dict | None:
    path = _pipeline_dir(data_dir, date) / "metadata.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def scheduled_publish_dates(data_dir: Path | str) -> set:
    """Return the set of local publish dates already taken by pipeline items."""
    base = Path(data_dir) / "pipeline"
    result: set = set()
    if not base.exists():
        return result
    for child in base.iterdir():
        meta = child / "metadata.json"
        if not meta.exists():
            continue
        item = json.loads(meta.read_text())
        pd = item.get("publish_date")
        if pd:
            result.add(date.fromisoformat(pd))
    return result
