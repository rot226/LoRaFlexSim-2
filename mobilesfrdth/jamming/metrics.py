"""Métriques agrégées propres aux campagnes de brouillage."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class JammingMetrics:
    """Résumé de l'impact du brouillage."""

    jammed_packets: int = 0
    total_packets: int = 0
    mean_jammer_power_dbm: float | None = None

    @property
    def jammed_ratio(self) -> float:
        return 0.0 if self.total_packets <= 0 else self.jammed_packets / self.total_packets


def summarize_jamming(*, jammed_flags: list[bool], jammer_powers_dbm: list[float] | None = None) -> JammingMetrics:
    """Agrège des indicateurs événementiels en métriques de campagne."""

    powers = jammer_powers_dbm or []
    return JammingMetrics(sum(1 for flag in jammed_flags if flag), len(jammed_flags), mean(powers) if powers else None)


def compute_packet_metrics(packet_events: Iterable[Mapping[str, Any] | Any]) -> dict[str, float | int]:
    """Calcule des métriques paquet en ignorant les événements de brouilleurs.

    Un événement est considéré comme légitime si ``traffic_type`` vaut
    ``"legitimate"`` ou si aucun ``jammer_id`` explicite n'est présent. Les
    réceptions dupliquées sont comptées dans ``rx_packets_total`` mais un même
    ``packet_id`` ne contribue qu'une seule fois au PDR.
    """

    tx_packets_total = 0
    rx_packets_total = 0
    rx_unique_packet_ids: set[Any] = set()

    for index, event in enumerate(packet_events):
        if not _is_legitimate_event(event):
            continue

        if _is_tx_event(event):
            tx_packets_total += 1

        if _is_rx_event(event):
            rx_packets_total += 1
            rx_unique_packet_ids.add(_event_value(event, "packet_id", default=("__missing_packet_id__", index)))

    rx_unique_packets_total = len(rx_unique_packet_ids)
    duplicate_packets_total = rx_packets_total - rx_unique_packets_total
    pdr_percent = 0.0 if tx_packets_total <= 0 else 100.0 * rx_unique_packets_total / tx_packets_total

    return {
        "tx_packets_total": tx_packets_total,
        "rx_packets_total": rx_packets_total,
        "rx_unique_packets_total": rx_unique_packets_total,
        "duplicate_packets_total": duplicate_packets_total,
        "pdr_percent": pdr_percent,
        "packet_loss_rate_percent": 100.0 - pdr_percent,
    }


def _event_value(event: Mapping[str, Any] | Any, key: str, *, default: Any = None) -> Any:
    if isinstance(event, Mapping):
        return event.get(key, default)
    return getattr(event, key, default)


def _is_legitimate_event(event: Mapping[str, Any] | Any) -> bool:
    traffic_type = _event_value(event, "traffic_type")
    if traffic_type is not None:
        return traffic_type == "legitimate"
    return _event_value(event, "jammer_id") is None


def _is_tx_event(event: Mapping[str, Any] | Any) -> bool:
    sent = _event_value(event, "sent")
    if sent is not None:
        return bool(sent)
    event_type = _normalized_event_type(event)
    return event_type in {"tx", "transmit", "transmitted", "sent", "send", "uplink"}


def _is_rx_event(event: Mapping[str, Any] | Any) -> bool:
    received = _event_value(event, "received")
    if received is not None:
        return bool(received)
    event_type = _normalized_event_type(event)
    return event_type in {"rx", "receive", "received", "delivered"}


def _normalized_event_type(event: Mapping[str, Any] | Any) -> str:
    for key in ("event_type", "type", "kind", "action"):
        value = _event_value(event, key)
        if value is not None:
            return str(value).lower()
    return ""


__all__ = ["JammingMetrics", "compute_packet_metrics", "summarize_jamming"]
