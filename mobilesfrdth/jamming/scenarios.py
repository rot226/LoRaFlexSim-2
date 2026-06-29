"""Scénarios de brouillage composables avec les campagnes mobilesfrdth."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .channel_selection import EU868_DEFAULT_CHANNELS_MHZ
from .jammer import JammerConfig
from .placement import circle_placement

BASELINE_JAMMING_SINGLE_CHANNEL = "baseline_jamming_single_channel"
MULTICHANNEL_JAMMING_ADR_CHANNEL_SELECTION = "multichannel_jamming_adr_channel_selection"
DEFAULT_ALLOWED_NODE_COUNTS = frozenset({20, 50, 100})
DEFAULT_SIM_TIME_S = 3600
DEFAULT_TX_POWER_DBM = 14
DEFAULT_BANDWIDTH_KHZ = 125
DEFAULT_INTERVAL_RANGE_S = (150, 200)
DEFAULT_INITIAL_SPREADING_FACTORS = tuple(range(7, 13))
SINGLE_CHANNEL_HZ = 868_100_000
EU868_CHANNELS_HZ = tuple(int(freq * 1_000_000) for freq in EU868_DEFAULT_CHANNELS_MHZ)


@dataclass(frozen=True)
class JammingScenarioParameters:
    """Paramètres communs validés pour les scénarios de brouillage."""

    node_count: int = 20
    allowed_node_counts: frozenset[int] = DEFAULT_ALLOWED_NODE_COUNTS
    sim_time_s: int = DEFAULT_SIM_TIME_S
    tx_power_dbm: int = DEFAULT_TX_POWER_DBM
    bandwidth_khz: int = DEFAULT_BANDWIDTH_KHZ
    interval_range_s: tuple[int, int] = DEFAULT_INTERVAL_RANGE_S
    initial_spreading_factors: tuple[int, ...] = DEFAULT_INITIAL_SPREADING_FACTORS

    def validate(self) -> None:
        """Valide les invariants partagés des scénarios demandés."""

        if self.node_count not in self.allowed_node_counts:
            allowed = ", ".join(str(value) for value in sorted(self.allowed_node_counts))
            raise ValueError(f"node_count={self.node_count!r} invalide; valeurs autorisées: {allowed}.")
        if self.sim_time_s != DEFAULT_SIM_TIME_S:
            raise ValueError(f"sim_time_s doit valoir {DEFAULT_SIM_TIME_S}.")
        if self.tx_power_dbm != DEFAULT_TX_POWER_DBM:
            raise ValueError(f"tx_power_dbm doit valoir {DEFAULT_TX_POWER_DBM}.")
        if self.bandwidth_khz != DEFAULT_BANDWIDTH_KHZ:
            raise ValueError(f"bandwidth_khz doit valoir {DEFAULT_BANDWIDTH_KHZ}.")
        if self.interval_range_s != DEFAULT_INTERVAL_RANGE_S:
            raise ValueError("interval_range_s doit définir l'intervalle uniforme 150–200 s.")
        if self.initial_spreading_factors != DEFAULT_INITIAL_SPREADING_FACTORS:
            raise ValueError("initial_spreading_factors doit couvrir SF7 à SF12.")

    def to_metadata(self) -> dict[str, Any]:
        """Retourne une représentation sérialisable des paramètres communs."""

        self.validate()
        return {
            "node_count": self.node_count,
            "allowed_node_counts": tuple(sorted(self.allowed_node_counts)),
            "sim_time_s": self.sim_time_s,
            "tx_power_dbm": self.tx_power_dbm,
            "bandwidth_khz": self.bandwidth_khz,
            "traffic_interval_distribution": "uniform",
            "traffic_interval_min_s": self.interval_range_s[0],
            "traffic_interval_max_s": self.interval_range_s[1],
            "initial_spreading_factors": self.initial_spreading_factors,
            "initial_spreading_factor_selection": "random",
        }


@dataclass(frozen=True)
class JammingScenario:
    """Description stable d'une extension de scénario avec brouilleurs."""

    name: str
    jammers: tuple[JammerConfig, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "scenario_name": self.name,
            "jammers": [j.__dict__ for j in self.jammers],
            "metadata": {"scenario_name": self.name, **dict(self.metadata)},
        }


def _common_parameters(
    *,
    node_count: int,
    allowed_node_counts: Iterable[int] = DEFAULT_ALLOWED_NODE_COUNTS,
    sim_time_s: int = DEFAULT_SIM_TIME_S,
    tx_power_dbm: int = DEFAULT_TX_POWER_DBM,
    bandwidth_khz: int = DEFAULT_BANDWIDTH_KHZ,
    interval_range_s: tuple[int, int] = DEFAULT_INTERVAL_RANGE_S,
    initial_spreading_factors: tuple[int, ...] = DEFAULT_INITIAL_SPREADING_FACTORS,
) -> JammingScenarioParameters:
    allowed = frozenset(allowed_node_counts)
    if not allowed:
        raise ValueError("allowed_node_counts ne doit pas être vide.")
    params = JammingScenarioParameters(
        node_count=node_count,
        allowed_node_counts=allowed,
        sim_time_s=sim_time_s,
        tx_power_dbm=tx_power_dbm,
        bandwidth_khz=bandwidth_khz,
        interval_range_s=interval_range_s,
        initial_spreading_factors=initial_spreading_factors,
    )
    params.validate()
    return params


def _scenario_metadata(name: str, params: JammingScenarioParameters, **extra: Any) -> dict[str, Any]:
    return {"scenario_name": name, **params.to_metadata(), **extra}


def no_jamming_scenario() -> JammingScenario:
    """Scénario témoin sans brouillage."""

    return JammingScenario(name="no_jamming", metadata={"scenario_name": "no_jamming"})


def baseline_jamming_single_channel(
    *,
    gateway_x: float,
    gateway_y: float,
    node_count: int = 20,
    allowed_node_counts: Iterable[int] = DEFAULT_ALLOWED_NODE_COUNTS,
    sim_time_s: int = DEFAULT_SIM_TIME_S,
    tx_power_dbm: int = DEFAULT_TX_POWER_DBM,
    bandwidth_khz: int = DEFAULT_BANDWIDTH_KHZ,
    interval_range_s: tuple[int, int] = DEFAULT_INTERVAL_RANGE_S,
    initial_spreading_factors: tuple[int, ...] = DEFAULT_INITIAL_SPREADING_FACTORS,
    start_angle_deg: float = 0.0,
) -> JammingScenario:
    """Scénario mono-canal: trafic légitime et brouillage à 868,1 MHz."""

    params = _common_parameters(
        node_count=node_count,
        allowed_node_counts=allowed_node_counts,
        sim_time_s=sim_time_s,
        tx_power_dbm=tx_power_dbm,
        bandwidth_khz=bandwidth_khz,
        interval_range_s=interval_range_s,
        initial_spreading_factors=initial_spreading_factors,
    )
    jammers = tuple(
        circle_placement(
            gateway_x=gateway_x,
            gateway_y=gateway_y,
            radius_m=10.0,
            count=6,
            start_angle_deg=start_angle_deg,
            tx_power_dbm=params.tx_power_dbm,
            channels_hz=(SINGLE_CHANNEL_HZ,),
        )
    )
    return JammingScenario(
        name=BASELINE_JAMMING_SINGLE_CHANNEL,
        jammers=jammers,
        metadata=_scenario_metadata(
            BASELINE_JAMMING_SINGLE_CHANNEL,
            params,
            legitimate_channels_hz=(SINGLE_CHANNEL_HZ,),
            jammer_channels_hz=(SINGLE_CHANNEL_HZ,),
            jammer_spreading_factors=DEFAULT_INITIAL_SPREADING_FACTORS,
            jammer_count=6,
            jammer_placement="circle",
            jammer_radius_m=10.0,
            traffic_targeting_mode="traffic_peak",
            synchronized=True,
            channel_selection="static",
        ),
    )


def multichannel_jamming_adr_channel_selection(
    *,
    gateway_x: float,
    gateway_y: float,
    node_count: int = 20,
    allowed_node_counts: Iterable[int] = DEFAULT_ALLOWED_NODE_COUNTS,
    sim_time_s: int = DEFAULT_SIM_TIME_S,
    tx_power_dbm: int = DEFAULT_TX_POWER_DBM,
    bandwidth_khz: int = DEFAULT_BANDWIDTH_KHZ,
    interval_range_s: tuple[int, int] = DEFAULT_INTERVAL_RANGE_S,
    initial_spreading_factors: tuple[int, ...] = DEFAULT_INITIAL_SPREADING_FACTORS,
    channel_selection: str = "adr-assisted",
    start_angle_deg: float = 0.0,
) -> JammingScenario:
    """Scénario multi-canal EU868 avec sélection de canal assistée par ADR."""

    params = _common_parameters(
        node_count=node_count,
        allowed_node_counts=allowed_node_counts,
        sim_time_s=sim_time_s,
        tx_power_dbm=tx_power_dbm,
        bandwidth_khz=bandwidth_khz,
        interval_range_s=interval_range_s,
        initial_spreading_factors=initial_spreading_factors,
    )
    jammers = tuple(
        circle_placement(
            gateway_x=gateway_x,
            gateway_y=gateway_y,
            radius_m=10.0,
            count=6,
            start_angle_deg=start_angle_deg,
            tx_power_dbm=params.tx_power_dbm,
            channels_hz=(SINGLE_CHANNEL_HZ,),
        )
    )
    return JammingScenario(
        name=MULTICHANNEL_JAMMING_ADR_CHANNEL_SELECTION,
        jammers=jammers,
        metadata=_scenario_metadata(
            MULTICHANNEL_JAMMING_ADR_CHANNEL_SELECTION,
            params,
            legitimate_channels_hz=EU868_CHANNELS_HZ,
            jammer_channels_hz=(SINGLE_CHANNEL_HZ,),
            jammer_count=6,
            jammer_placement="circle",
            jammer_radius_m=10.0,
            channel_selection=channel_selection,
        ),
    )


def circle_static_jamming_scenario(
    *,
    gateway_x: float,
    gateway_y: float,
    radius_m: float = 10.0,
    number_of_jammers: int = 6,
    start_angle_deg: float = 0.0,
) -> JammingScenario:
    """Scénario avec brouilleurs statiques placés en cercle autour de la gateway."""

    return JammingScenario(
        name="circle_static_jamming",
        jammers=tuple(
            circle_placement(
                gateway_x=gateway_x,
                gateway_y=gateway_y,
                radius_m=radius_m,
                count=number_of_jammers,
                start_angle_deg=start_angle_deg,
            )
        ),
        metadata={"scenario_name": "circle_static_jamming", "placement": "circle", "radius_m": radius_m, "start_angle_deg": start_angle_deg},
    )


def circle_shifted_jamming_scenario(
    *,
    gateway_x: float,
    gateway_y: float,
    radius_m: float = 10.0,
    number_of_jammers: int = 6,
    start_angle_deg: float = 30.0,
) -> JammingScenario:
    """Scénario circulaire décalé pour comparer deux anneaux de brouilleurs."""

    return JammingScenario(
        name="circle_shifted_jamming",
        jammers=tuple(
            circle_placement(
                gateway_x=gateway_x,
                gateway_y=gateway_y,
                radius_m=radius_m,
                count=number_of_jammers,
                start_angle_deg=start_angle_deg,
            )
        ),
        metadata={"scenario_name": "circle_shifted_jamming", "placement": "circle", "radius_m": radius_m, "start_angle_deg": start_angle_deg},
    )
