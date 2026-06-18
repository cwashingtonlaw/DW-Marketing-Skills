"""Load secret values from the environment or a local secrets file."""
from __future__ import annotations

import json
import os
from pathlib import Path


def _default_secrets_path() -> Path:
    return Path.home() / ".config/ge-video/secrets.json"


def get_secret(name: str, config_path: Path | str | None = None) -> str:
    env_value = os.environ.get(name)
    if env_value:
        return env_value

    path = Path(config_path) if config_path else _default_secrets_path()
    if path.exists():
        data = json.loads(path.read_text())
        if name in data:
            return data[name]

    raise KeyError(name)
