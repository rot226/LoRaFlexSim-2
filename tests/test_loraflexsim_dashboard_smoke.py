from __future__ import annotations

import importlib


def test_dashboard_module_imports_and_exposes_layout() -> None:
    dashboard = importlib.import_module("loraflexsim.launcher.dashboard")

    assert getattr(dashboard, "dashboard", None) is not None
    assert callable(getattr(dashboard.dashboard, "servable", None))
