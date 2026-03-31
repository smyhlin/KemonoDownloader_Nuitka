import os
from types import SimpleNamespace

from kemonodownloader import creator_downloader as cd


def teardown_module(module):
    # Clean any thread-local or cached state that could leak between tests
    try:
        cd._user_agent = None
    except Exception:
        pass
    try:
        cd.HEADERS = None
    except Exception:
        pass
    try:
        cd._thread_local.__dict__.clear()
    except Exception:
        pass


def test_get_user_agent_fallback(monkeypatch):
    # Force UserAgent to raise so fallback is used
    cd._user_agent = None

    class FakeUA:
        def __init__(self):
            raise RuntimeError("no ua")

    monkeypatch.setattr("kemonodownloader.creator_downloader.UserAgent", FakeUA)
    ua = cd.get_user_agent()
    assert isinstance(ua, str)
    assert "Mozilla" in ua
    # reset
    cd._user_agent = None


def test_get_domain_config():
    cfg = cd.get_domain_config("https://coomer.st/user/1")
    assert cfg["domain"] == "coomer.st"
    assert cfg["base_url"].startswith("https://coomer.st")

    cfg2 = cd.get_domain_config("https://kemono.cr/some/path")
    assert cfg2["domain"] == "kemono.cr"


def test_get_headers_caching():
    cd.HEADERS = None
    h1 = cd.get_headers()
    assert isinstance(h1, dict)
    h2 = cd.get_headers()
    assert h1 is h2
    # cleanup
    cd.HEADERS = None


def test_get_session_thread_local_and_socks(monkeypatch):
    # Reset thread local storage
    cd._thread_local.__dict__.clear()

    s1 = cd.get_session(None)
    s2 = cd.get_session(None)
    assert s1 is s2

    class S:
        def get_proxy_settings(self):
            return {"http": "socks5://127.0.0.1:9050"}

    socks_session = cd.get_session(S())
    # socks_session should be stored on thread local
    assert getattr(cd._thread_local, "socks_session", None) is not None
    assert getattr(cd._thread_local, "socks_session") is socks_session

    # calling again returns same socks session instance
    socks_session2 = cd.get_session(S())
    assert socks_session is socks_session2
    # cleanup
    cd._thread_local.__dict__.clear()


def test_sanitize_filename_various():
    assert cd.sanitize_filename("") == "unnamed"
    assert cd.sanitize_filename("name...") == "name"
    assert cd.sanitize_filename("te st") == "te_st"
    bad = "a" * 120
    short = cd.sanitize_filename(bad, max_length=50)
    assert len(short) <= 50


def test_generate_filename_and_folder_and_auto_rename(tmp_path, qapp, monkeypatch):
    # Monkeypatch HashDB to avoid filesystem DB interactions
    class DummyHashDB:
        def __init__(self, other_files_dir):
            pass

        def lookup(self, *a, **k):
            return None

        def store(self, *a, **k):
            return None

    monkeypatch.setattr(cd, "HashDB", DummyHashDB)

    file_url = "https://kemono.cr/some/path/orig.jpg?f=orig.jpg"
    files_to_download = [file_url]
    files_to_posts_map = {file_url: "42"}

    th = cd.CreatorDownloadThread(
        service="fanbox",
        creator_id="123",
        download_folder=str(tmp_path),
        selected_posts=["42"],
        files_to_download=files_to_download,
        files_to_posts_map=files_to_posts_map,
        console=None,
        other_files_dir=str(tmp_path / "other"),
        post_titles_map={},
        auto_rename_enabled=True,
        settings=None,
        max_concurrent=1,
        download_text=False,
    )

    target_folder, filename = th.generate_filename_and_folder(
        file_url, str(tmp_path), 0, 1, "42", "My Title"
    )

    # Filename should include auto-rename prefix and post id/orig name
    assert filename.endswith(".jpg")
    assert filename.startswith("1_")

    # Target folder should contain creator folder and per-post folder
    expected_creator = os.path.join(str(tmp_path), "123_123")
    assert expected_creator in target_folder
    # When no title exists in post_titles_map the implementation falls back
    # to a Post_{post_id} title — assert that fallback is used.
    assert os.path.join("42_Post_42") in target_folder

    # second call increments auto-rename counter
    target2, filename2 = th.generate_filename_and_folder(
        file_url, str(tmp_path), 1, 1, "42", "My Title"
    )
    assert filename2.startswith("2_")


def test_get_desc_folder_for_post_respects_strategy(tmp_path, qapp, monkeypatch):
    class DummyHashDB:
        def __init__(self, other_files_dir):
            pass

        def lookup(self, *a, **k):
            return None

        def store(self, *a, **k):
            return None

    monkeypatch.setattr(cd, "HashDB", DummyHashDB)

    class Settings:
        def __init__(self, strat):
            self.settings_tab = SimpleNamespace(
                get_creator_folder_strategy=lambda: strat
            )

    th = cd.CreatorDownloadThread(
        service="fanbox",
        creator_id="123",
        download_folder=str(tmp_path),
        selected_posts=["42"],
        files_to_download=[],
        files_to_posts_map={},
        console=None,
        other_files_dir=str(tmp_path / "other"),
        post_titles_map={},
        auto_rename_enabled=False,
        settings=Settings("per_post"),
        max_concurrent=1,
        download_text=False,
    )

    creator_folder = os.path.join(str(tmp_path), "123_123")
    desc = th.get_desc_folder_for_post(creator_folder, "42", "My Title")
    assert desc.endswith(os.path.join("42_My_Title"))

    th2 = cd.CreatorDownloadThread(
        service="fanbox",
        creator_id="123",
        download_folder=str(tmp_path),
        selected_posts=["42"],
        files_to_download=[],
        files_to_posts_map={},
        console=None,
        other_files_dir=str(tmp_path / "other"),
        post_titles_map={},
        auto_rename_enabled=False,
        settings=Settings("by_file_type"),
        max_concurrent=1,
        download_text=False,
    )
    desc2 = th2.get_desc_folder_for_post(creator_folder, "42", "My Title")
    assert desc2.endswith(os.path.join("txt"))

    th3 = cd.CreatorDownloadThread(
        service="fanbox",
        creator_id="123",
        download_folder=str(tmp_path),
        selected_posts=["42"],
        files_to_download=[],
        files_to_posts_map={},
        console=None,
        other_files_dir=str(tmp_path / "other"),
        post_titles_map={},
        auto_rename_enabled=False,
        settings=Settings("single_folder"),
        max_concurrent=1,
        download_text=False,
    )
    desc3 = th3.get_desc_folder_for_post(creator_folder, "42", "My Title")
    assert desc3 == os.path.normpath(creator_folder)
