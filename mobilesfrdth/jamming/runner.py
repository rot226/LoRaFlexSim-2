"""Runner événementiel pour simulations LoRa avec fenêtres de brouillage.

Ce module construit uniquement le trafic légitime, applique ensuite les effets
radio/temporels des brouilleurs par croisement de fenêtres, et retourne des
structures sérialisables pour l'analyse des campagnes de brouillage.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
import math
import random
from typing import Any, Callable, Iterable, Mapping, Sequence

from mobilesfrdth.simulator.engine import Event, EventDrivenEngine, Node

from .channel_selection import ChannelSet, EU868_DEFAULT_CHANNELS_MHZ
from .jammer import JammingEvent
from .jammer_scheduler import JammerWindow


@dataclass(frozen=True)
class LegitimateNode:
    """Nœud légitime placé autour d'une gateway."""

    node_id: int
    x_m: float
    y_m: float
    period_s: float
    payload_size: int
    sf: int
    tx_power_dbm: float
    frequency_mhz: float
    channel_id: int


@dataclass(frozen=True)
class JammingRunResult:
    """Résultat complet d'un run de brouillage.

    ``raw_events`` ne contient que des paquets/événements légitimes enrichis :
    les fenêtres ou émissions des brouilleurs sont conservées séparément dans le
    résumé et ne sont jamais comptées comme paquets légitimes.
    """

    raw_events: list[dict[str, Any]]
    metrics_by_node: dict[int, dict[str, Any]]
    channel_sf_timeseries: list[dict[str, Any]]
    run_summary: dict[str, Any]
    legitimate_nodes: list[LegitimateNode] = field(default_factory=list)


def build_legitimate_nodes(
    *,
    node_count: int,
    gateway_x_m: float = 0.0,
    gateway_y_m: float = 0.0,
    radius_m: float = 1_000.0,
    period_s: float | tuple[float, float] = 60.0,
    payload_size: int = 12,
    tx_power_dbm: float = 14.0,
    channels_mhz: Sequence[float] = tuple(EU868_DEFAULT_CHANNELS_MHZ[:3]),
    spreading_factors: Sequence[int] = (7, 8, 9, 10, 11, 12),
    rng: random.Random,
) -> list[LegitimateNode]:
    """Construit des nœuds légitimes uniformément distribués dans un disque."""

    if node_count < 0:
        raise ValueError("node_count doit être positif ou nul.")
    if radius_m < 0:
        raise ValueError("radius_m doit être positif ou nul.")
    if not channels_mhz:
        raise ValueError("channels_mhz ne peut pas être vide.")
    if not spreading_factors:
        raise ValueError("spreading_factors ne peut pas être vide.")

    channel_set = ChannelSet([float(freq) for freq in channels_mhz])
    nodes: list[LegitimateNode] = []
    for node_id in range(1, node_count + 1):
        # sqrt(U) garantit une densité uniforme en surface dans le disque.
        distance = radius_m * math.sqrt(rng.random())
        angle = rng.uniform(0.0, 2.0 * math.pi)
        frequency_mhz = float(rng.choice(list(channel_set.frequencies_mhz)))
        node_period_s = rng.uniform(*period_s) if isinstance(period_s, tuple) else float(period_s)
        nodes.append(
            LegitimateNode(
                node_id=node_id,
                x_m=gateway_x_m + distance * math.cos(angle),
                y_m=gateway_y_m + distance * math.sin(angle),
                period_s=node_period_s,
                payload_size=int(payload_size),
                sf=int(rng.choice(list(spreading_factors))),
                tx_power_dbm=float(tx_power_dbm),
                frequency_mhz=frequency_mhz,
                channel_id=channel_set.channel_id_for_frequency(frequency_mhz),
            )
        )
    return nodes


def run_jamming_simulation(
    *,
    node_count: int,
    until_s: float,
    seed: int | None = None,
    gateway_id: str = "gw0",
    gateway_x_m: float = 0.0,
    gateway_y_m: float = 0.0,
    radius_m: float = 1_000.0,
    period_s: float | tuple[float, float] = 60.0,
    payload_size: int = 12,
    tx_power_dbm: float = 14.0,
    channels_mhz: Sequence[float] = tuple(EU868_DEFAULT_CHANNELS_MHZ[:3]),
    spreading_factors: Sequence[int] = (7, 8, 9, 10, 11, 12),
    jamming_windows: Iterable[JammerWindow | JammingEvent | Mapping[str, Any]] | None = None,
    progress_callback: Callable[[float, dict], None] | None = None,
    mode: str = "snir_on",
    algo: str = "adr",
    **engine_kwargs: Any,
) -> JammingRunResult:
    """Exécute un run reproductible et applique les effets de brouillage."""

    rng = random.Random(seed)
    legitimate_nodes = build_legitimate_nodes(
        node_count=node_count,
        gateway_x_m=gateway_x_m,
        gateway_y_m=gateway_y_m,
        radius_m=radius_m,
        period_s=period_s,
        payload_size=payload_size,
        tx_power_dbm=tx_power_dbm,
        channels_mhz=channels_mhz,
        spreading_factors=spreading_factors,
        rng=rng,
    )
    sim_nodes = [
        Node(
            node_id=n.node_id,
            period_s=n.period_s,
            payload_size=n.payload_size,
            meta={
                "x_m": n.x_m,
                "y_m": n.y_m,
                "sf": n.sf,
                "tx_power_dbm": n.tx_power_dbm,
                "frequency_mhz": n.frequency_mhz,
                "channel_id": n.channel_id,
            },
        )
        for n in legitimate_nodes
    ]

    try:
        engine_result = EventDrivenEngine(seed=seed).run(nodes=sim_nodes, until_s=until_s, mode=mode, algo=algo, **engine_kwargs)
        raw_engine_events = engine_result.events
    except (AttributeError, TypeError, ValueError):
        raw_engine_events = _minimal_legitimate_events(sim_nodes, until_s=until_s)

    normalized_windows = [_normalize_window(window) for window in (jamming_windows or [])]
    raw_events = _enrich_legitimate_events(
        raw_engine_events=raw_engine_events,
        nodes_by_id={node.node_id: node for node in legitimate_nodes},
        gateway_id=gateway_id,
        jamming_windows=normalized_windows,
        progress_callback=progress_callback,
        until_s=until_s,
        node_count=node_count,
        seed=seed,
    )
    metrics_by_node = _metrics_by_node(raw_events)
    timeseries = _channel_sf_timeseries(raw_events)
    summary = _run_summary(raw_events, metrics_by_node, normalized_windows, seed, until_s)
    return JammingRunResult(raw_events, metrics_by_node, timeseries, summary, legitimate_nodes)


def _minimal_legitimate_events(nodes: list[Node], *, until_s: float) -> list[Event]:
    events: list[Event] = []
    for node in nodes:
        t = 0.0
        while t <= until_s:
            sf = int(node.meta.get("sf", 7))
            events.append(Event(time_s=t, kind="uplink", node_id=node.node_id, sf=sf, success=True, delivered=True, payload_bytes=node.payload_size, airtime_s=EventDrivenEngine._airtime_s(sf=sf, payload_size=node.payload_size), outage=False))
            t += max(node.period_s, 1e-6)
    return events


def _normalize_window(window: JammerWindow | JammingEvent | Mapping[str, Any]) -> dict[str, Any]:
    data = asdict(window) if is_dataclass(window) else dict(window)
    start = float(data.get("start_s", data.get("time_s", 0.0)))
    end = float(data.get("end_s", start + float(data.get("duration_s", 0.0))))
    freq = data.get("frequency_mhz")
    if freq is None and data.get("frequency_hz") is not None:
        freq = float(data["frequency_hz"]) / 1_000_000.0
    return {**data, "start_s": start, "end_s": end, "sf": data.get("sf"), "frequency_mhz": freq}


def _enrich_legitimate_events(
    *,
    raw_engine_events: list[Event],
    nodes_by_id: dict[int, LegitimateNode],
    gateway_id: str,
    jamming_windows: list[dict[str, Any]],
    progress_callback: Callable[[float, dict], None] | None,
    until_s: float,
    node_count: int,
    seed: int | None,
) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    packet_seq = 0
    rx_packets = 0
    jammed_packets = 0
    next_progress_bucket = 0
    for event in raw_engine_events:
        if event.kind != "uplink" or event.node_id not in nodes_by_id:
            continue
        node = nodes_by_id[event.node_id]
        packet_seq += 1
        sf = int(getattr(event, "sf", node.sf))
        jammed = _is_jammed(event.time_s, event.time_s + max(float(getattr(event, "airtime_s", 0.0)), 0.0), sf, node.frequency_mhz, jamming_windows)
        received_without_jam = bool(getattr(event, "delivered", getattr(event, "success", False)))
        received = received_without_jam and not jammed
        collided = bool(getattr(event, "success", True) is False) and not jammed
        enriched.append({
            **event.__dict__,
            "packet_id": f"legit-{event.node_id}-{packet_seq}",
            "frequency_mhz": node.frequency_mhz,
            "channel_id": node.channel_id,
            "sf": sf,
            "tx_power_dbm": node.tx_power_dbm,
            "sent": True,
            "received": received,
            "lost": not received,
            "collided": collided,
            "jammed": jammed,
            "delay_s": float(getattr(event, "airtime_s", 0.0)),
            "gateway_id": gateway_id,
        })
        rx_packets += int(received)
        jammed_packets += int(jammed)
        if progress_callback is not None:
            progress = _progress_for_time(event.time_s, until_s)
            bucket = int(progress * 100)
            if bucket >= next_progress_bucket:
                _emit_progress(
                    progress_callback,
                    progress,
                    time_s=float(event.time_s),
                    until_s=until_s,
                    node_count=node_count,
                    seed=seed,
                    tx_packets=packet_seq,
                    rx_packets=rx_packets,
                    jammed_packets=jammed_packets,
                )
                next_progress_bucket = bucket + 1
    if progress_callback is not None:
        _emit_progress(
            progress_callback,
            1.0,
            time_s=until_s,
            until_s=until_s,
            node_count=node_count,
            seed=seed,
            tx_packets=packet_seq,
            rx_packets=rx_packets,
            jammed_packets=jammed_packets,
        )
    return enriched


def _progress_for_time(time_s: float, until_s: float) -> float:
    if until_s <= 0.0:
        return 1.0
    return min(max(float(time_s) / float(until_s), 0.0), 1.0)


def _emit_progress(
    progress_callback: Callable[[float, dict], None],
    progress: float,
    *,
    time_s: float,
    until_s: float,
    node_count: int,
    seed: int | None,
    tx_packets: int,
    rx_packets: int,
    jammed_packets: int,
) -> None:
    context = {
        "time_s": float(time_s),
        "until_s": float(until_s),
        "node_count": int(node_count),
        "seed": seed,
        "tx_packets": int(tx_packets),
        "rx_packets": int(rx_packets),
        "jammed_packets": int(jammed_packets),
    }
    progress_callback(min(max(float(progress), 0.0), 1.0), context)


def _is_jammed(start_s: float, end_s: float, sf: int, frequency_mhz: float, windows: list[dict[str, Any]]) -> bool:
    for window in windows:
        if end_s <= float(window["start_s"]) or start_s >= float(window["end_s"]):
            continue
        window_sf = window.get("sf")
        window_freq = window.get("frequency_mhz")
        sf_matches = window_sf is None or int(window_sf) == int(sf)
        freq_matches = window_freq is None or abs(float(window_freq) - float(frequency_mhz)) <= 1e-6
        if sf_matches and freq_matches:
            return True
    return False


def _metrics_by_node(events: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    metrics: dict[int, dict[str, Any]] = {}
    for event in events:
        m = metrics.setdefault(int(event["node_id"]), {"sent": 0, "received": 0, "lost": 0, "collided": 0, "jammed": 0, "mean_delay_s": 0.0})
        for key in ("sent", "received", "lost", "collided", "jammed"):
            m[key] += int(bool(event[key]))
        m["mean_delay_s"] += float(event["delay_s"])
    for m in metrics.values():
        m["pdr"] = 0.0 if m["sent"] == 0 else m["received"] / m["sent"]
        m["jammed_ratio"] = 0.0 if m["sent"] == 0 else m["jammed"] / m["sent"]
        m["mean_delay_s"] = 0.0 if m["sent"] == 0 else m["mean_delay_s"] / m["sent"]
    return metrics


def _channel_sf_timeseries(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[int, int, int], dict[str, Any]] = {}
    for event in events:
        key = (int(event["time_s"]), int(event["channel_id"]), int(event["sf"]))
        bucket = buckets.setdefault(key, {"time_s": key[0], "channel_id": key[1], "sf": key[2], "sent": 0, "received": 0, "lost": 0, "jammed": 0})
        for field_name in ("sent", "received", "lost", "jammed"):
            bucket[field_name] += int(bool(event[field_name]))
    return [buckets[key] for key in sorted(buckets)]


def _run_summary(events: list[dict[str, Any]], metrics_by_node: dict[int, dict[str, Any]], windows: list[dict[str, Any]], seed: int | None, until_s: float) -> dict[str, Any]:
    sent = sum(int(e["sent"]) for e in events)
    received = sum(int(e["received"]) for e in events)
    return {
        "seed": seed,
        "until_s": until_s,
        "legitimate_packet_count": sent,
        "received_packets": received,
        "lost_packets": sent - received,
        "jammed_packets": sum(int(e["jammed"]) for e in events),
        "pdr": 0.0 if sent == 0 else received / sent,
        "node_count": len(metrics_by_node),
        "jamming_window_count": len(windows),
        "jamming_windows": windows,
    }


__all__ = ["JammingRunResult", "LegitimateNode", "build_legitimate_nodes", "run_jamming_simulation"]
