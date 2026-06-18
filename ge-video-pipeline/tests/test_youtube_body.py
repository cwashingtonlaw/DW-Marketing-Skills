from gevideo.youtube import build_video_body, DEFAULT_CATEGORY_ID


def test_body_structure_schedules_as_private():
    body = build_video_body(
        title="My Short", description="desc", tags=["a", "b"],
        publish_at="2026-06-20T17:00:00Z",
    )
    assert body["snippet"]["title"] == "My Short"
    assert body["snippet"]["description"] == "desc"
    assert body["snippet"]["tags"] == ["a", "b"]
    assert body["snippet"]["categoryId"] == DEFAULT_CATEGORY_ID
    assert body["status"]["privacyStatus"] == "private"
    assert body["status"]["publishAt"] == "2026-06-20T17:00:00Z"
    assert body["status"]["selfDeclaredMadeForKids"] is False


def test_category_and_kids_overridable():
    body = build_video_body(
        title="t", description="", tags=[], publish_at="2026-06-20T17:00:00Z",
        category_id="25", made_for_kids=True,
    )
    assert body["snippet"]["categoryId"] == "25"
    assert body["status"]["selfDeclaredMadeForKids"] is True


def test_tags_are_copied_not_aliased():
    tags = ["a"]
    body = build_video_body(title="t", description="", tags=tags,
                            publish_at="2026-06-20T17:00:00Z")
    tags.append("b")
    assert body["snippet"]["tags"] == ["a"]
