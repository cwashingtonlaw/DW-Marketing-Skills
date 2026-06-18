import json

import gevideo.cli as cli
from gevideo.queue import (
    create_pipeline_item, save_pipeline_item, load_pipeline_item,
)


def _write_config(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"avatar_id": "av_1", "voice_id": "vo_1"}))
    return cfg


def test_heygen_generate_renders_and_updates_item(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    item = create_pipeline_item(date="2026-06-18", topic={"id": "t", "title": "Hook"})
    save_pipeline_item(data_dir, item)

    script_file = tmp_path / "script.txt"
    script_file.write_text("Read this aloud.")
    cfg = _write_config(tmp_path)
    monkeypatch.setenv("HEYGEN_API_KEY", "KEY")

    captured = {}

    def fake_generate_to_file(client, **kwargs):
        captured.update(kwargs)
        # simulate the download the real function performs
        from pathlib import Path
        Path(kwargs["dest_path"]).parent.mkdir(parents=True, exist_ok=True)
        Path(kwargs["dest_path"]).write_bytes(b"MP4")
        return {"video_id": "vid123", "video_url": "u", "duration": 30.0}

    monkeypatch.setattr(cli.heygen, "generate_to_file", fake_generate_to_file)

    code = cli.main([
        "--data-dir", str(data_dir), "heygen-generate",
        "--date", "2026-06-18", "--script-file", str(script_file),
        "--config", str(cfg),
    ])

    assert code == 0
    assert captured["script"] == "Read this aloud."
    assert captured["avatar_id"] == "av_1"
    assert captured["voice_id"] == "vo_1"

    updated = load_pipeline_item(data_dir, "2026-06-18")
    expected_path = str(data_dir / "pipeline" / "2026-06-18" / "video.mp4")
    assert updated["video_path"] == expected_path
    assert updated["metadata"]["heygen_video_id"] == "vid123"


def test_heygen_generate_missing_item_returns_nonzero(tmp_path, monkeypatch):
    script_file = tmp_path / "script.txt"
    script_file.write_text("x")
    cfg = _write_config(tmp_path)
    monkeypatch.setenv("HEYGEN_API_KEY", "KEY")

    code = cli.main([
        "--data-dir", str(tmp_path / "data"), "heygen-generate",
        "--date", "2099-01-01", "--script-file", str(script_file),
        "--config", str(cfg),
    ])
    assert code == 1
