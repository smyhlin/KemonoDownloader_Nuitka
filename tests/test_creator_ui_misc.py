import os
from types import SimpleNamespace

from kemonodownloader import creator_downloader as cd


def test_logs_window_download_and_clear(tmp_path, monkeypatch):
    from PyQt6.QtWidgets import QWidget

    parent = QWidget()
    parent.creator_console = SimpleNamespace(
        toHtml=lambda: "<p>log</p>", clear=lambda: setattr(parent, "cleared", True)
    )

    def append_log(msg, level):
        parent.appended = (msg, level)

    parent.append_log_to_console = append_log

    logs = cd.LogsWindow(parent)

    # Set some content and monkeypatch the file dialog to return a path
    logs.logs_display.setPlainText("line1\nline2")
    out_path = str(tmp_path / "out.txt")
    monkeypatch.setattr(
        "kemonodownloader.creator_downloader.QFileDialog.getSaveFileName",
        lambda *a, **k: (out_path, ""),
    )

    logs.download_logs()
    assert os.path.exists(out_path)
    assert hasattr(parent, "appended")

    # Test clear_logs clears both views
    logs.logs_display.setPlainText("something")
    logs.clear_logs()
    assert logs.logs_display.toPlainText() == ""
    assert getattr(parent, "cleared", False) is True


def test_image_modal_display_and_progress(monkeypatch):
    # Create an uninitialized ImageModal to test its methods directly
    modal = cd.ImageModal.__new__(cd.ImageModal)
    from PyQt6.QtGui import QPixmap
    from PyQt6.QtWidgets import QLabel, QProgressBar

    modal._progress_bar = QProgressBar()
    modal._label = QLabel()

    # update_progress should set value and label text
    modal.update_progress(42)
    assert modal._progress_bar.value() == 42

    # display_image should set a pixmap on the label
    pix = QPixmap(10, 10)
    pix.fill()
    modal.display_image("http://x", pix)
    assert modal._label.pixmap() is not None

    # display_error should set label text and call QMessageBox.critical
    called = {}

    def fake_critical(*a, **k):
        called["ok"] = True

    monkeypatch.setattr(
        "kemonodownloader.creator_downloader.QMessageBox.critical",
        fake_critical,
    )
    modal.display_error("some error")
    assert called.get("ok") is True
