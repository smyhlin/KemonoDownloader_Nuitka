import gzip
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import kemonodownloader.creator_downloader as cd


def make_gzipped_response(obj):
    j = json.dumps(obj).encode("utf-8")
    return gzip.compress(j)


def test_post_detection_with_list(monkeypatch):
    settings = SimpleNamespace(
        creator_posts_max_attempts=1, settings_tab=SimpleNamespace()
    )

    post = {
        "id": "p1",
        "title": "T1",
        "file": {"path": "/media/1.png", "name": "img1.png"},
    }

    class Resp:
        status_code = 200
        content = make_gzipped_response([post])

    class S:
        def get(self, *a, **k):
            return Resp()

    monkeypatch.setattr(cd, "get_session", lambda st: S())

    post_titles = {}
    t = cd.PostDetectionThread(
        "https://kemono.cr/artist/user/10", post_titles, settings
    )
    t.posts_batch = SimpleNamespace(emit=MagicMock())
    t.finished = SimpleNamespace(emit=MagicMock())
    t.log = SimpleNamespace(emit=MagicMock())
    t.error = SimpleNamespace(emit=MagicMock())

    t.run()

    assert t.posts_batch.emit.called
    assert t.finished.emit.called


def test_post_detection_with_dict_posts(monkeypatch):
    settings = SimpleNamespace(
        creator_posts_max_attempts=1, settings_tab=SimpleNamespace()
    )

    post = {
        "id": "p2",
        "title": "T2",
        "attachments": [{"path": "/att/2.jpg", "name": "a2.jpg"}],
    }

    class Resp:
        status_code = 200
        content = make_gzipped_response({"posts": [post]})

    class S:
        def get(self, *a, **k):
            return Resp()

    monkeypatch.setattr(cd, "get_session", lambda st: S())

    post_titles = {}
    t = cd.PostDetectionThread(
        "https://kemono.cr/artist/user/11", post_titles, settings
    )
    t.posts_batch = SimpleNamespace(emit=MagicMock())
    t.finished = SimpleNamespace(emit=MagicMock())
    t.log = SimpleNamespace(emit=MagicMock())
    t.error = SimpleNamespace(emit=MagicMock())

    t.run()

    assert t.posts_batch.emit.called
    assert t.finished.emit.called


def test_post_detection_invalid_url_emits_error():
    settings = SimpleNamespace(
        creator_posts_max_attempts=1, settings_tab=SimpleNamespace()
    )
    post_titles = {}
    t = cd.PostDetectionThread("https://kemono.cr/invalid/path", post_titles, settings)
    t.error = SimpleNamespace(emit=MagicMock())
    t.log = SimpleNamespace(emit=MagicMock())

    t.run()

    assert t.error.emit.called
