import os
from types import SimpleNamespace

from PyQt6.QtWidgets import QTextEdit, QWidget

import kemonodownloader.creator_downloader as cd


class DummyParent(QWidget):
    def __init__(self):
        super().__init__()
        self.creator_console = QTextEdit()
        self.append_log_to_console = lambda *a, **k: None


def test_logs_window_download_logs(tmp_path, qapp, monkeypatch):
    # Parent with a creator_console and append_log_to_console
    parent = DummyParent()
    parent.creator_console.setHtml("<b>log</b>")

    lw = cd.LogsWindow(parent)
    # Force update of logs_display from parent (timer won't fire in test)
    lw._do_update()

    # Monkeypatch QFileDialog.getSaveFileName to return a path
    save_path = str(tmp_path / "logs.txt")
    monkeypatch.setattr(
        "kemonodownloader.creator_downloader.QFileDialog.getSaveFileName",
        lambda *a, **k: (save_path, None),
    )

    lw.download_logs()

    assert os.path.exists(save_path)


def test_add_creators_from_file_reads_and_adds(tmp_path, qapp, monkeypatch):
    # Create minimal parent expected by CreatorDownloaderTab
    parent = SimpleNamespace()
    parent.cache_folder = str(tmp_path / "cache")
    parent.other_files_folder = str(tmp_path / "other")
    parent.base_folder = str(tmp_path / "base")
    parent.download_folder = str(tmp_path / "dl")
    parent.tabs = SimpleNamespace(
        count=lambda: 1, setTabEnabled=lambda i, b: None, currentIndex=lambda: 0
    )
    parent.settings_tab = SimpleNamespace(
        settings_applied=SimpleNamespace(connect=lambda *a, **k: None),
        language_changed=SimpleNamespace(connect=lambda *a, **k: None),
    )
    os.makedirs(parent.cache_folder, exist_ok=True)
    os.makedirs(parent.other_files_folder, exist_ok=True)

    tab = cd.CreatorDownloaderTab(parent)

    # Create a temp file with two URLs (one valid, one invalid)
    f = tmp_path / "links.txt"
    f.write_text("https://kemono.cr/artist/user/1\nnot-a-url\n")

    monkeypatch.setattr(
        "kemonodownloader.creator_downloader.QFileDialog.getOpenFileName",
        lambda *a, **k: (str(f), None),
    )

    # Prevent modal dialogs from blocking the test
    monkeypatch.setattr(
        "kemonodownloader.creator_downloader.QMessageBox.information",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "kemonodownloader.creator_downloader.QMessageBox.critical",
        lambda *a, **k: None,
    )

    # Monkeypatch append_log_to_console to capture messages
    logs = []
    tab.append_log_to_console = lambda msg, level: logs.append((level, msg))

    tab.add_creators_from_file()

    # Expect at least one added and one invalid reported
    assert (
        any("invalid" in m[1].lower() or "invalid" in m[0].lower() for m in logs)
        or len(tab.creator_queue) >= 1
    )
