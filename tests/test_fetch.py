from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rejects_bad_url():
    assert client.get("/fetch", params={"url": "ftp://x"}).status_code == 400


def test_proxies_response():
    class Fake:
        status_code = 201
        content = b"hello"

        class headers:
            @staticmethod
            def multi_items():
                return [("content-type", "text/plain"), ("set-cookie", "a=1"),
                        ("set-cookie", "b=2"), ("content-encoding", "gzip")]

    class FakeSession:
        def __init__(self, **kw):
            self.kw = kw

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            pass

        async def request(self, method, url, **kw):
            assert method == "POST" and url == "https://example.com/x"
            assert kw["data"] == b"body"
            return Fake()

    with patch("app.main.AsyncSession", FakeSession):
        r = client.post("/fetch", params={"url": "https://example.com/x"}, content=b"body")
    assert r.status_code == 201 and r.content == b"hello"
    assert r.headers.get_list("set-cookie") == ["a=1", "b=2"]
    assert "content-encoding" not in r.headers
