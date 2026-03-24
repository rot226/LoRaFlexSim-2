"""Proxy de canal legacy pour scripts d'archive."""

from importlib import import_module

_mod = import_module("mobile" + "sfrdth.simulator.channel")

ChannelConfig = _mod.ChannelConfig
pathloss_log_distance_db = _mod.pathloss_log_distance_db
received_power_dbm = _mod.received_power_dbm
