"""HeyGen text-to-avatar video client (v2 generate / v1 status)."""
from __future__ import annotations

BASE_URL = "https://api.heygen.com"
MAX_INPUT_TEXT = 1500  # HeyGen v2 input_text hard limit


def build_generate_payload(*, script: str, avatar_id: str, voice_id: str,
                           title: str, width: int = 720, height: int = 1280,
                           speed: float = 1.0, test: bool = False,
                           background: str = "#FFFFFF") -> dict:
    if len(script) > MAX_INPUT_TEXT:
        raise ValueError(
            f"script is {len(script)} chars; HeyGen limit is {MAX_INPUT_TEXT}")
    return {
        "title": title,
        "caption": False,
        "test": test,
        "dimension": {"width": width, "height": height},
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal",
                },
                "voice": {
                    "type": "text",
                    "input_text": script,
                    "voice_id": voice_id,
                    "speed": speed,
                },
                "background": {"type": "color", "value": background},
            }
        ],
    }
