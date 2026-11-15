"""Initial scaffold tests."""

import importlib


def test_import_backend_app():
    """Verify backend.app imports cleanly."""
    app_module = importlib.import_module("backend.app")
    config_module = importlib.import_module("backend.app.config")
    assert app_module is not None
    assert config_module.settings is not None
    assert config_module.settings.DATABASE_URL.startswith("sqlite")

