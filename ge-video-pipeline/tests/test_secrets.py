import json

import pytest

from gevideo.secrets import get_secret


def test_env_var_takes_precedence(tmp_path, monkeypatch):
    secrets_file = tmp_path / "secrets.json"
    secrets_file.write_text(json.dumps({"HEYGEN_API_KEY": "from-file"}))
    monkeypatch.setenv("HEYGEN_API_KEY", "from-env")

    assert get_secret("HEYGEN_API_KEY", config_path=secrets_file) == "from-env"


def test_falls_back_to_secrets_file(tmp_path, monkeypatch):
    secrets_file = tmp_path / "secrets.json"
    secrets_file.write_text(json.dumps({"HEYGEN_API_KEY": "from-file"}))
    monkeypatch.delenv("HEYGEN_API_KEY", raising=False)

    assert get_secret("HEYGEN_API_KEY", config_path=secrets_file) == "from-file"


def test_missing_secret_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("HEYGEN_API_KEY", raising=False)
    assert not (tmp_path / "secrets.json").exists()
    with pytest.raises(KeyError):
        get_secret("HEYGEN_API_KEY", config_path=tmp_path / "secrets.json")
