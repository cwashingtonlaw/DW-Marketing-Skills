import pytest

from gevideo.heygen import build_generate_payload, MAX_INPUT_TEXT


def test_payload_has_verified_structure():
    payload = build_generate_payload(
        script="Hello there.", avatar_id="av_1", voice_id="vo_1",
        title="My Short", width=720, height=1280, speed=1.0,
    )
    assert payload["title"] == "My Short"
    assert payload["test"] is False
    assert payload["caption"] is False
    assert payload["dimension"] == {"width": 720, "height": 1280}

    inp = payload["video_inputs"][0]
    assert inp["character"]["type"] == "avatar"
    assert inp["character"]["avatar_id"] == "av_1"
    assert inp["character"]["avatar_style"] == "normal"
    assert inp["voice"]["type"] == "text"
    assert inp["voice"]["voice_id"] == "vo_1"
    assert inp["voice"]["input_text"] == "Hello there."
    assert inp["voice"]["speed"] == 1.0


def test_test_flag_can_be_set_true():
    payload = build_generate_payload(
        script="x", avatar_id="a", voice_id="v", title="t", test=True,
    )
    assert payload["test"] is True


def test_script_over_limit_raises():
    too_long = "a" * (MAX_INPUT_TEXT + 1)
    with pytest.raises(ValueError):
        build_generate_payload(script=too_long, avatar_id="a", voice_id="v", title="t")


def test_script_at_limit_is_allowed():
    ok = "a" * MAX_INPUT_TEXT
    payload = build_generate_payload(script=ok, avatar_id="a", voice_id="v", title="t")
    assert payload["video_inputs"][0]["voice"]["input_text"] == ok
