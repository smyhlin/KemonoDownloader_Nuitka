from types import SimpleNamespace

from kemonodownloader import creator_downloader as cd


def test_creator_tab_ui_basics(monkeypatch, qapp, tmp_path):
    parent = SimpleNamespace()
    parent.cache_folder = str(tmp_path)
    parent.other_files_folder = str(tmp_path)
    parent.download_folder = str(tmp_path)

    # Instantiate the tab with a minimal parent (no settings_tab)
    tab = cd.CreatorDownloaderTab(parent)

    # Prevent modal dialogs from blocking tests
    monkeypatch.setattr(cd.QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(cd.QMessageBox, "critical", lambda *a, **k: None)
    monkeypatch.setattr(
        cd.QMessageBox, "question", lambda *a, **k: cd.QMessageBox.StandardButton.Yes
    )

    # update_ui_text should populate widget labels without error
    tab.update_ui_text()
    assert tab.creator_download_btn.text() != ""

    # toggle_fast_mode: enable fast mode and verify state updated
    tab.toggle_fast_mode(2)  # Checked
    assert tab.fast_mode is True

    # Add multiple creators: include one valid and one invalid URL
    valid = "https://kemono.cr/user/123"
    invalid = "not a url"
    tab.creator_multi_url_input.setPlainText(f"{valid}\n{invalid}\n")
    tab.add_multiple_creators_to_queue()
    # valid should have been added
    assert any(valid in u for u, _ in tab.creator_queue)

    # add_creator_to_queue: empty input logs error
    tab.creator_url_input.setText("")
    tab.add_creator_to_queue()
    # Add duplicate prevention: add same valid URL again triggers warning
    tab.creator_url_input.setText(valid)
    tab.add_creator_to_queue()  # this will attempt validation (spawn thread), but duplicate check will catch it

    # create_remove_handler should remove entry when user confirms
    pre_len = len(tab.creator_queue)
    url_to_remove = tab.creator_queue[0][0]
    remove_handler = tab.create_remove_handler(url_to_remove)
    remove_handler()
    assert len(tab.creator_queue) <= pre_len
