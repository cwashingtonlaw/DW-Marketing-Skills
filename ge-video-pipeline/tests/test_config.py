import json
from pathlib import Path

from gevideo.config import Config, load_config


def test_load_config_applies_defaults_for_missing_keys(tmp_path):
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps({"avatar_id": "av_1", "voice_id": "vo_1"}))

    cfg = load_config(cfg_file)

    assert cfg.avatar_id == "av_1"
    assert cfg.voice_id == "vo_1"
    assert cfg.publish_time == "12:00"
    assert cfg.timezone == "America/Chicago"
    assert cfg.buffer_days == 3
    assert cfg.backlog_low_threshold == 5


def test_load_config_overrides_defaults(tmp_path):
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps({
        "avatar_id": "av_1", "voice_id": "vo_1",
        "publish_time": "09:30", "timezone": "America/New_York",
        "buffer_days": 7, "backlog_low_threshold": 10,
        "data_dir": "/tmp/ge-video-data",
    }))

    cfg = load_config(cfg_file)

    assert cfg.publish_time == "09:30"
    assert cfg.timezone == "America/New_York"
    assert cfg.buffer_days == 7
    assert cfg.backlog_low_threshold == 10
    assert cfg.data_dir == Path("/tmp/ge-video-data")


def test_load_config_data_dir_defaults_to_local_share():
    # When data_dir is absent, it expands under the user's home.
    cfg = Config(avatar_id="a", voice_id="v")
    assert cfg.data_dir == Path.home() / ".local/share/ge-video"
