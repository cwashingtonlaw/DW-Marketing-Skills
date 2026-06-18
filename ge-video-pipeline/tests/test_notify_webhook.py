from gevideo.notify import post_chat_webhook


class FakePoster:
    def __init__(self):
        self.calls = []

    def post(self, url, payload):
        self.calls.append((url, payload))
        return 200


def test_post_chat_webhook_sends_text_payload():
    poster = FakePoster()
    status = post_chat_webhook("https://chat.example/hook", "hello", http=poster)

    assert status == 200
    url, payload = poster.calls[0]
    assert url == "https://chat.example/hook"
    assert payload == {"text": "hello"}
