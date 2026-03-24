from __future__ import annotations

import importlib


def test_import_loraflexsim_public_api() -> None:
    module = importlib.import_module("loraflexsim")

    assert module.__all__ == [
        "LoRaMAC",
        "LoRaPHY",
        "Application",
        "Node",
        "Gateway",
        "NetworkServer",
    ]
    for exported_name in module.__all__:
        assert getattr(module, exported_name) is not None
