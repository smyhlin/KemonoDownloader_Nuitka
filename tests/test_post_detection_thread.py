import gzip
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import kemonodownloader.creator_downloader as cd


class Resp:
    def __init__(self, content_bytes, text=""):
        self.content = content_bytes
        self._text = text
        self.status_code = 200

    @property
    def text(self):
        return self._text

    def close(self):
        return None


def _mk_signal_mock():
    return SimpleNamespace(emit=MagicMock())


def test_post_detection_plain_json(monkeypatch):
    posts = [{"id": "1", "title": "Hello", "file": {"path": "/img/p.jpg"}}]
    text = json.dumps(posts)
    resp = Resp(text.encode("utf-8"), text=text)

    class S:
        def get(self, *a, **k):
            return resp

    monkeypatch.setattr(cd, "get_session", lambda st=None: S())

    post_titles_map = {}
    settings = SimpleNamespace(creator_posts_max_attempts=1, settings_tab=None)
    t = cd.PostDetectionThread("https://kemono.cr/user/1", post_titles_map, settings)
    t.log = _mk_signal_mock()
    t.posts_batch = _mk_signal_mock()
    t.finished = _mk_signal_mock()
    t.run()

    # Ensure titles map populated and finished emitted
    assert any(k[1] == "1" and k[2] == "1" for k in post_titles_map.keys())
    assert t.finished.emit.called


def test_post_detection_gzipped_response(monkeypatch):
    posts = [{"id": "2", "title": "Gzip", "attachments": []}]
    text = json.dumps(posts)
    gz = gzip.compress(text.encode("utf-8"))
    resp = Resp(gz, text="")

    class S:
        def get(self, *a, **k):
            return resp

    monkeypatch.setattr(cd, "get_session", lambda st=None: S())

    post_titles_map = {}
    settings = SimpleNamespace(creator_posts_max_attempts=1, settings_tab=None)
    t = cd.PostDetectionThread("https://kemono.cr/user/2", post_titles_map, settings)
    t.log = _mk_signal_mock()
    t.posts_batch = _mk_signal_mock()
    t.finished = _mk_signal_mock()
    t.run()

    assert any(k[1] == "2" and k[2] == "2" for k in post_titles_map.keys())
    assert t.finished.emit.called
