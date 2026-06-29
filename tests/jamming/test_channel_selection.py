from __future__ import annotations

from types import SimpleNamespace
import random

import pytest

from mobilesfrdth.jamming.channel_selection import (
    EU868_DEFAULT_CHANNELS_MHZ,
    AdrAssistedChannelSelectionPolicy,
    ChannelSet,
    DegradationAwareChannelSelectionPolicy,
    RandomChannelSelectionPolicy,
    StaticChannelSelectionPolicy,
    build_channel_selection_policy,
)


def test_channel_set_eu868_ids() -> None:
    channels = ChannelSet(EU868_DEFAULT_CHANNELS_MHZ)

    assert channels.channel_id_for_frequency(868.1) == 0
    assert channels.channel_id_for_frequency(867.9) == 7


def test_static_policy_keeps_current_channel() -> None:
    node = SimpleNamespace(current_frequency_mhz=868.3, adr_enabled=False)

    selected = StaticChannelSelectionPolicy().select_channel(
        node,
        ChannelSet(EU868_DEFAULT_CHANNELS_MHZ),
        random.Random(1),
        {},
    )

    assert selected == 868.3


def test_random_policy_blocks_migration_without_adr_override() -> None:
    node = SimpleNamespace(current_frequency_mhz=868.1, adr_enabled=False)

    with pytest.raises(PermissionError, match="migrations"):
        RandomChannelSelectionPolicy().select_channel(
            node,
            ChannelSet([868.3]),
            random.Random(1),
            {},
        )


def test_adr_assisted_requires_adr_or_explicit_override() -> None:
    node = SimpleNamespace(current_frequency_mhz=868.1, adr_enabled=False, adr_channel_id=1)

    with pytest.raises(PermissionError, match="adr-assisted"):
        AdrAssistedChannelSelectionPolicy().select_channel(
            node,
            ChannelSet(EU868_DEFAULT_CHANNELS_MHZ),
            random.Random(1),
            {},
        )

    selected = AdrAssistedChannelSelectionPolicy().select_channel(
        node,
        ChannelSet(EU868_DEFAULT_CHANNELS_MHZ),
        random.Random(1),
        {"allow_channel_selection_without_adr": True},
    )
    assert selected == 868.3


def test_degradation_aware_prefers_least_degraded_channel() -> None:
    selected = DegradationAwareChannelSelectionPolicy().select_channel(
        SimpleNamespace(adr_enabled=True),
        ChannelSet([868.1, 868.3, 868.5]),
        random.Random(1),
        {"channel_degradation": {868.1: 5.0, 868.3: 1.0, 868.5: 3.0}},
    )

    assert selected == 868.3


def test_policy_factory() -> None:
    assert build_channel_selection_policy("degradation-aware").name == "degradation-aware"
