"""Load non-secret pipeline configuration from a JSON file."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


def _default_data_dir() -> Path:
    return Path.home() / ".local/share/ge-video"


@dataclass
class Config:
    avatar_id: str
    voice_id: str
    channel_id: str = ""
    publish_time: str = "12:00"          # local HH:MM
    timezone: str = "America/Chicago"
    buffer_days: int = 3                 # keep this many days scheduled ahead
    backlog_low_threshold: int = 5       # warn when ready topics drop below this
    data_dir: Path = field(default_factory=_default_data_dir)


def load_config(path: Path | str) -> Config:
    data = json.loads(Path(path).read_text())
    data_dir = data.get("data_dir")
    return Config(
        avatar_id=data["avatar_id"],
        voice_id=data["voice_id"],
        channel_id=data.get("channel_id", ""),
        publish_time=data.get("publish_time", "12:00"),
        timezone=data.get("timezone", "America/Chicago"),
        buffer_days=data.get("buffer_days", 3),
        backlog_low_threshold=data.get("backlog_low_threshold", 5),
        data_dir=Path(data_dir) if data_dir else _default_data_dir(),
    )
