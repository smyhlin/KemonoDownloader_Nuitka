import importlib
from types import SimpleNamespace

from kemonodownloader.kd_settings import SettingsTab


def test_get_proxy_settings_none_when_disabled():
    fake = SimpleNamespace(
        settings={"use_proxy": False},
        temp_settings={"use_proxy": False},
        tor_process=None,
    )
    assert SettingsTab.get_proxy_settings(fake) is None


def test_get_proxy_settings_custom_proxy():
    fake = SimpleNamespace(
        settings={
            "use_proxy": True,
            "proxy_type": "custom",
            "custom_proxy_url": "http://1.2.3.4:8080",
        },
        temp_settings={"use_proxy": False},
        tor_process=None,
    )
    proxies = SettingsTab.get_proxy_settings(fake)
    assert proxies == {"http": "http://1.2.3.4:8080", "https": "http://1.2.3.4:8080"}


def test_get_proxy_settings_tor_not_running():
    fake = SimpleNamespace(
        settings={"use_proxy": True, "proxy_type": "tor"},
        temp_settings={"use_proxy": False},
        tor_process=None,
    )
    assert SettingsTab.get_proxy_settings(fake) is None


def test_get_proxy_settings_tor_with_socks(monkeypatch):
    from kemonodownloader import kd_settings

    # Simulate tor process running
    fake_proc = SimpleNamespace(state=lambda: kd_settings.QProcess.ProcessState.Running)
    fake = SimpleNamespace(
        settings={"use_proxy": True, "proxy_type": "tor"},
        temp_settings={"use_proxy": False},
        tor_process=fake_proc,
    )

    # Monkeypatch find_spec to pretend socks is available
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: object())

    proxies = SettingsTab.get_proxy_settings(fake)
    assert proxies is not None
    assert proxies["http"].startswith("socks") or proxies["http"].startswith("http")
