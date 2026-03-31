import importlib
from types import SimpleNamespace

from kemonodownloader import kd_settings as ks


def make_tab(tmp_path):
    parent = SimpleNamespace()
    parent.base_folder = str(tmp_path / "base")
    parent.download_folder = str(tmp_path / "base" / "Downloads")
    parent.cache_folder = str(tmp_path / "base" / "Cache")
    parent.other_files_folder = str(tmp_path / "base" / "Other Files")
    parent.ensure_folders_exist = lambda: None
    parent.post_tab = SimpleNamespace()
    parent.creator_tab = SimpleNamespace()
    return ks.SettingsTab(parent)


def test_get_proxy_settings_tor_fallback(tmp_path, monkeypatch):
    tab = make_tab(tmp_path)
    tab.temp_settings["use_proxy"] = True
    tab.temp_settings["proxy_type"] = "tor"

    class FakeProc:
        def state(self):
            from PyQt6.QtCore import QProcess

            return QProcess.ProcessState.Running

    tab.tor_process = FakeProc()

    # Simulate missing socks package so code falls back to HTTP proxy
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: None)

    proxies = tab.get_proxy_settings()
    assert proxies is not None
    assert proxies.get("http").startswith("http")


def test_auto_detect_tor_returns_none_when_not_found(tmp_path):
    tab = make_tab(tmp_path)
    # Ensure temp_settings points to a tmp base directory that does not contain tor
    tab.temp_settings["base_directory"] = str(tmp_path / "no_tor")
    res = tab.auto_detect_tor()
    assert res is None
