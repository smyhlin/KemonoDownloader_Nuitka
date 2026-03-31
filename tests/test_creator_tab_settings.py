from types import SimpleNamespace

from kemonodownloader import creator_downloader as cd


def test_create_thread_settings_defaults():
    tab = cd.CreatorDownloaderTab.__new__(cd.CreatorDownloaderTab)
    tab._parent = None
    ts = tab._create_thread_settings()
    assert ts.creator_posts_max_attempts == 1
    assert ts.settings_tab is None


def test_create_thread_settings_from_parent():
    parent = SimpleNamespace()

    class FakeSettingsTab:
        def get_creator_posts_max_attempts(self):
            return 10

        def get_post_data_max_retries(self):
            return 4

        def get_file_download_max_retries(self):
            return 3

        def get_api_request_max_retries(self):
            return 2

        def get_simultaneous_downloads(self):
            return 7

    parent.settings_tab = FakeSettingsTab()
    tab = cd.CreatorDownloaderTab.__new__(cd.CreatorDownloaderTab)
    tab._parent = parent
    ts = tab._create_thread_settings()
    assert ts.creator_posts_max_attempts == 10
    assert ts.post_data_max_retries == 4
    assert ts.simultaneous_downloads == 7
