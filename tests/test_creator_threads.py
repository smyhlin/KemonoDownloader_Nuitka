from types import SimpleNamespace
from unittest.mock import MagicMock

import kemonodownloader.creator_downloader as cd


def _mk_signal_mock():
    return SimpleNamespace(emit=MagicMock())


def test_post_population_thread_maps_posts(qapp):
    detected_posts = [("Title1", (1, "thumb1")), ("Title2", (2, "thumb2"))]
    t = cd.PostPopulationThread(detected_posts)
    t.finished = _mk_signal_mock()
    t.log = _mk_signal_mock()
    t.run()
    expected = {
        "Title1 (ID: 1)": (1, "thumb1"),
        "Title2 (ID: 2)": (2, "thumb2"),
    }
    t.finished.emit.assert_called_once_with(expected, detected_posts)


def test_filter_thread_runs(qapp):
    all_detected = [("First Post", (1, "u1")), ("Other", (2, "u2"))]
    checked = {1: True, 2: False}
    t = cd.FilterThread(all_detected, checked, "first")
    t.finished = _mk_signal_mock()
    t.log = _mk_signal_mock()
    t.run()
    filtered = [("First Post", 1, "u1", True)]
    t.finished.emit.assert_called_once_with(filtered)


def test_checkbox_toggle_thread(qapp):
    visible = [("A", (1, "u1")), ("B", (2, "u2"))]
    checked = {1: False, 2: False}
    t = cd.CheckboxToggleThread(visible, checked, 2)
    t.finished = _mk_signal_mock()
    t.log = _mk_signal_mock()
    t.run()
    # Inspect the emitted args
    assert t.finished.emit.called
    new_checked, posts_to_download = t.finished.emit.call_args[0]
    assert new_checked[1] is True and new_checked[2] is True
    assert set(posts_to_download) == {1, 2}


def test_validation_thread_invalid_url(qapp):
    settings = SimpleNamespace(api_request_max_retries=1, settings_tab=None)
    t = cd.ValidationThread("http://bad/url", settings)
    t.log = _mk_signal_mock()
    t.result = _mk_signal_mock()
    t.run()
    t.result.emit.assert_called_with(False)


def test_validation_thread_success(monkeypatch, qapp):
    settings = SimpleNamespace(api_request_max_retries=1, settings_tab=None)

    class Resp:
        status_code = 200

        @property
        def text(self):
            return "This page mentions kemono somewhere"

    class S:
        def get(self, url, headers=None, timeout=None):
            return Resp()

    monkeypatch.setattr(cd, "get_session", lambda st: S())
    t = cd.ValidationThread("https://kemono.cr/user/1", settings)
    t.log = _mk_signal_mock()
    t.result = _mk_signal_mock()
    t.run()
    t.result.emit.assert_called_with(True)
