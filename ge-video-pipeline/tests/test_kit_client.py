import pytest

from gevideo.kit import KitClient, KitError


class FakeHttp:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def post_json(self, url, headers, payload):
        self.calls.append((url, headers, payload))
        return self.result


def test_create_broadcast_returns_id_and_sends_key():
    http = FakeHttp({"broadcast": {"id": 64}})
    client = KitClient("KEY", http=http)

    bid = client.create_broadcast({"subject": "s"})

    assert bid == 64
    url, headers, payload = http.calls[0]
    assert url == "https://api.kit.com/v4/broadcasts"
    assert headers["X-Kit-Api-Key"] == "KEY"
    assert payload == {"subject": "s"}


def test_create_broadcast_raises_on_errors():
    http = FakeHttp({"errors": ["invalid params"]})
    client = KitClient("KEY", http=http)
    with pytest.raises(KitError):
        client.create_broadcast({"subject": "s"})


def test_make_default_client_is_callable():
    from gevideo import kit
    assert callable(kit.make_default_client)
