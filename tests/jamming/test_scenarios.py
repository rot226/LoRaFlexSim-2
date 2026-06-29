from __future__ import annotations

import csv
import math

import pytest

from mobilesfrdth.jamming.csv_exporter import export_jamming_rows
from mobilesfrdth.jamming.scenarios import (
    BASELINE_JAMMING_SINGLE_CHANNEL,
    EU868_CHANNELS_HZ,
    MULTICHANNEL_JAMMING_ADR_CHANNEL_SELECTION,
    SINGLE_CHANNEL_HZ,
    baseline_jamming_single_channel,
    multichannel_jamming_adr_channel_selection,
)


def test_baseline_jamming_single_channel_defaults() -> None:
    scenario = baseline_jamming_single_channel(gateway_x=100.0, gateway_y=200.0)

    assert scenario.name == BASELINE_JAMMING_SINGLE_CHANNEL
    assert scenario.metadata["scenario_name"] == BASELINE_JAMMING_SINGLE_CHANNEL
    assert scenario.metadata["legitimate_channels_hz"] == (SINGLE_CHANNEL_HZ,)
    assert scenario.metadata["jammer_channels_hz"] == (SINGLE_CHANNEL_HZ,)
    assert scenario.metadata["traffic_targeting_mode"] == "traffic_peak"
    assert scenario.metadata["synchronized"] is True
    assert scenario.metadata["sim_time_s"] == 3600
    assert scenario.metadata["tx_power_dbm"] == 14
    assert scenario.metadata["bandwidth_khz"] == 125
    assert (scenario.metadata["traffic_interval_min_s"], scenario.metadata["traffic_interval_max_s"]) == (150, 200)
    assert scenario.metadata["initial_spreading_factors"] == (7, 8, 9, 10, 11, 12)
    assert len(scenario.jammers) == 6
    assert {jammer.channels_hz for jammer in scenario.jammers} == {(SINGLE_CHANNEL_HZ,)}
    assert {jammer.tx_power_dbm for jammer in scenario.jammers} == {14}
    for jammer in scenario.jammers:
        assert math.hypot(jammer.x_m - 100.0, jammer.y_m - 200.0) == pytest.approx(10.0)


def test_multichannel_jamming_uses_eu868_and_adr_default() -> None:
    scenario = multichannel_jamming_adr_channel_selection(gateway_x=0.0, gateway_y=0.0)

    assert scenario.name == MULTICHANNEL_JAMMING_ADR_CHANNEL_SELECTION
    assert scenario.metadata["legitimate_channels_hz"] == EU868_CHANNELS_HZ
    assert len(scenario.metadata["legitimate_channels_hz"]) == 8
    assert scenario.metadata["jammer_channels_hz"] == (SINGLE_CHANNEL_HZ,)
    assert scenario.metadata["channel_selection"] == "adr-assisted"
    assert {jammer.channels_hz for jammer in scenario.jammers} == {(SINGLE_CHANNEL_HZ,)}


def test_node_count_default_validation_is_extensible() -> None:
    with pytest.raises(ValueError, match="node_count"):
        baseline_jamming_single_channel(gateway_x=0.0, gateway_y=0.0, node_count=30)

    scenario = baseline_jamming_single_channel(
        gateway_x=0.0,
        gateway_y=0.0,
        node_count=30,
        allowed_node_counts={20, 30, 50, 100},
    )
    assert scenario.metadata["node_count"] == 30


def test_export_jamming_rows_adds_scenario_name(tmp_path) -> None:
    output = export_jamming_rows([{"scenario": "legacy", "pdr": 0.9}], tmp_path / "rows.csv")

    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows == [{"pdr": "0.9", "scenario": "legacy", "scenario_name": "legacy"}]
