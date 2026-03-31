def test_main_exec_calls_exit(monkeypatch):
    import importlib

    app_mod = importlib.import_module("kemonodownloader.app")

    # Dummy QApplication that records exec() call and returns 0
    class DummyApp:
        def __init__(self, argv):
            self.argv = argv

        def setStyle(self, _):
            pass

        def exec(self):
            return 0

    # Dummy main window with show()
    class DummyWindow:
        def show(self):
            pass

    monkeypatch.setattr(app_mod, "QApplication", lambda argv: DummyApp(argv))
    monkeypatch.setattr(app_mod, "load_bundled_fonts", lambda: None)
    monkeypatch.setattr(app_mod, "KemonoDownloader", lambda *a, **k: DummyWindow())

    called = {}

    def fake_exit(code=0):
        called["code"] = code

    monkeypatch.setattr(app_mod.sys, "exit", fake_exit)

    # Call main() and ensure sys.exit was invoked with the app exec return value
    app_mod.main()
    assert called.get("code") == 0
