import hashlib
import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import requests

import kemonodownloader.post_downloader as pd


def test_preview_thread_uses_cached_file(tmp_path, monkeypatch):
    url = "https://kemono.cr/media/1.png"
    ext = os.path.splitext(url)[1]
    cache_key = hashlib.md5(url.encode()).hexdigest() + ext
    cache_dir = str(tmp_path / "cache")
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, cache_key)
    # Create a dummy file (content doesn't need to be a valid image because
    # we will mock QPixmap.load to accept it)
    with open(cache_path, "wb") as f:
        f.write(b"dummy")

    class MockPixmap:
        def __init__(self):
            pass

        def load(self, path):
            return True

    monkeypatch.setattr(pd, "QPixmap", MockPixmap)

    t = pd.PreviewThread(url, cache_dir, settings_tab=None)
    t.preview_ready = SimpleNamespace(emit=MagicMock())
    t.progress = SimpleNamespace(emit=MagicMock())
    t.error = SimpleNamespace(emit=MagicMock())

    t.run()

    assert t.preview_ready.emit.called


def test_preview_thread_request_exception(monkeypatch):
    url = "https://kemono.cr/media/2.png"
    cache_dir = "/tmp/nonexistent"

    class S:
        def get(self, *a, **k):
            raise requests.RequestException("fail")

    monkeypatch.setattr(pd, "get_session", lambda st: S())
    t = pd.PreviewThread(url, cache_dir, settings_tab=None)
    t.preview_ready = SimpleNamespace(emit=MagicMock())
    t.progress = SimpleNamespace(emit=MagicMock())
    t.error = SimpleNamespace(emit=MagicMock())

    t.run()

    assert t.error.emit.called


def test_downloadthread_request_exception(monkeypatch, tmp_path):
    settings = SimpleNamespace(
        file_download_max_retries=1, api_request_max_retries=1, settings_tab=None
    )
    download_folder = str(tmp_path / "dl")
    os.makedirs(download_folder, exist_ok=True)
    other = str(tmp_path / "other")
    os.makedirs(other, exist_ok=True)
    file_url = "https://kemono.cr/media/3.png?f=f3.png"

    dt = pd.DownloadThread(
        "https://kemono.cr/artist/user/1/post/1",
        download_folder,
        [file_url],
        {file_url: "1"},
        MagicMock(),
        other,
        "1",
        settings,
        max_concurrent=1,
    )

    class S:
        def get(self, *a, **k):
            raise requests.RequestException("network")

    monkeypatch.setattr(pd, "get_session", lambda st: S())

    dt.file_progress = SimpleNamespace(emit=MagicMock())
    dt.file_completed = SimpleNamespace(emit=MagicMock())
    dt.log = SimpleNamespace(emit=MagicMock())

    dt.download_file(file_url, download_folder, 0, 1)

    assert dt.file_completed.emit.called
