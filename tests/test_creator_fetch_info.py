from types import SimpleNamespace

from kemonodownloader.creator_downloader import (
    CreatorDownloadThread,
    ThreadSettings,
    sanitize_filename,
)


class FakeResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code

    def json(self):
        return self._data


class FakeSession:
    def __init__(self, profile_name, posts):
        self.profile_name = profile_name
        self.posts = posts

    def get(self, url, *args, **kwargs):
        if url.endswith("/profile"):
            return FakeResponse({"name": self.profile_name}, 200)
        for pid, title in self.posts.items():
            if url.endswith(f"/post/{pid}"):
                return FakeResponse({"title": title}, 200)
        return FakeResponse({}, 404)


def make_settings():
    settings_tab = SimpleNamespace(
        get_creator_filename_template=lambda: None,
        get_creator_folder_strategy=lambda: "per_post",
        get_proxy_settings=lambda: None,
    )
    return ThreadSettings(
        creator_posts_max_attempts=1,
        post_data_max_retries=1,
        file_download_max_retries=1,
        api_request_max_retries=1,
        simultaneous_downloads=1,
        settings_tab=settings_tab,
    )


def test_fetch_creator_and_post_info_populates(monkeypatch, tmp_path):
    download_folder = str(tmp_path / "out")
    other_files_dir = str(tmp_path / "other")
    file_url = "https://kemono.cr/files/x.png"
    files_to_download = [file_url]
    files_to_posts_map = {file_url: "1"}

    settings = make_settings()
    thread = CreatorDownloadThread(
        service="svc",
        creator_id="creator123",
        download_folder=download_folder,
        selected_posts=["1"],
        files_to_download=files_to_download,
        files_to_posts_map=files_to_posts_map,
        console=None,
        other_files_dir=other_files_dir,
        post_titles_map={},
        auto_rename_enabled=False,
        settings=settings,
        download_text=False,
    )

    monkeypatch.setattr(
        "kemonodownloader.creator_downloader.get_session",
        lambda settings_tab=None: FakeSession("Creator Name", {"1": "Post Title"}),
    )

    thread.fetch_creator_and_post_info()

    assert thread.creator_name
    key = ("svc", "creator123", "1")
    assert key in thread.post_titles_map
    assert thread.post_titles_map[key] == sanitize_filename("Post Title")
