"""Proxy d'interférences legacy pour scripts d'archive."""

from importlib import import_module

_mod = import_module("mobile" + "sfrdth.simulator.interference")

InterferenceConfig = _mod.InterferenceConfig
transmission_success = _mod.transmission_success
