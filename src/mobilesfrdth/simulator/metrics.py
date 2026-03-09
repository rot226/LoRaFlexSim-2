"""Calcul explicite des métriques de simulation mobilesfrdth."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence


_EPSILON = 1e-12


def _safe_denominator(value: float) -> float:
    return value if value > _EPSILON else _EPSILON


def pdr(delivered_packets: int, transmitted_packets: int) -> float:
    """Packet Delivery Ratio.

    Formule explicite: ``PDR = delivered_packets / transmitted_packets``.
    """

    return float(delivered_packets) / _safe_denominator(float(transmitted_packets))


def der(delivered_packets: int, generated_packets: int) -> float:
    """Data Extraction Ratio.

    Formule explicite: ``DER = delivered_packets / generated_packets``.
    """

    return float(delivered_packets) / _safe_denominator(float(generated_packets))


def throughput(delivered_bytes: int, duration_s: float) -> float:
    """Débit utile en bit/s.

    Formule explicite: ``throughput = 8 * delivered_bytes / duration_s``.
    """

    return (8.0 * float(delivered_bytes)) / _safe_denominator(float(duration_s))


def convergence_tc(
    samples: Sequence[float],
    *,
    dt_s: float,
    target: float | None = None,
    moving_window_bins: int = 3,
    stationary_tail_bins: int = 5,
    target_ratio: float = 0.9,
) -> float:
    """Temps de convergence ``Tc`` d'une série temporelle.

    La métrique est d'abord lissée par moyenne glissante de taille
    ``moving_window_bins``. Le régime stationnaire est estimé comme la moyenne des
    ``stationary_tail_bins`` derniers points de cette métrique lissée (ou moins si la
    série est courte). On cherche ensuite le premier indice ``i`` tel que:
    ``smoothed[i] >= target_ratio * stationary_estimate``.

    Le paramètre ``target`` reste possible pour forcer une cible explicite.

    Formule explicite: ``Tc = i * dt_s``.
    Retourne ``inf`` si non convergé.
    """

    if not samples:
        return math.inf
    if dt_s <= 0:
        raise ValueError("dt_s doit être > 0")
    if moving_window_bins < 1:
        raise ValueError("moving_window_bins doit être >= 1")
    if stationary_tail_bins < 1:
        raise ValueError("stationary_tail_bins doit être >= 1")
    if target_ratio <= 0:
        raise ValueError("target_ratio doit être > 0")

    smoothed: list[float] = []
    for idx in range(len(samples)):
        start = max(0, idx - moving_window_bins + 1)
        window = samples[start : idx + 1]
        smoothed.append(sum(window) / len(window))

    stationary_window = smoothed[-min(stationary_tail_bins, len(smoothed)) :]
    stationary_estimate = target if target is not None else (sum(stationary_window) / len(stationary_window))
    threshold = target_ratio * stationary_estimate

    start_index = min(moving_window_bins - 1, len(smoothed) - 1)
    for idx in range(start_index, len(smoothed)):
        if smoothed[idx] >= threshold:
            return float(idx) * float(dt_s)
    return math.inf


def jain_fairness(values: Iterable[float]) -> float:
    """Indice d'équité de Jain.

    Formule explicite: ``J = (sum(x_i)^2) / (n * sum(x_i^2))``.
    """

    data = [float(v) for v in values]
    if not data:
        return 0.0
    numerator = sum(data) ** 2
    denominator = len(data) * sum(v * v for v in data)
    if denominator <= _EPSILON:
        return 0.0
    return numerator / denominator


def airtime_lora(
    payload_bytes: int,
    *,
    sf: int,
    bw_hz: int = 125000,
    coding_rate: int = 1,
    preamble_symbols: int = 8,
    crc: int = 1,
    explicit_header: int = 1,
    low_data_rate_optimize: int | None = None,
) -> float:
    """Airtime LoRa (Time-on-Air) en secondes.

    Formules explicites:
    - ``T_sym = 2**sf / bw_hz``
    - ``N_payload = 8 + max(ceil((8*PL - 4*SF + 28 + 16*CRC - 20*IH)/(4*(SF-2*DE))) * (CR+4), 0)``
    - ``T_packet = (N_preamble + 4.25 + N_payload) * T_sym``
    """

    if sf < 6:
        raise ValueError("sf invalide")
    if bw_hz <= 0:
        raise ValueError("bw_hz doit être > 0")

    de = low_data_rate_optimize
    if de is None:
        de = 1 if sf >= 11 and bw_hz == 125000 else 0

    t_sym = (2**sf) / float(bw_hz)
    numerator = 8 * payload_bytes - 4 * sf + 28 + 16 * crc - 20 * (1 - explicit_header)
    denominator = 4 * (sf - 2 * de)
    payload_symbols_term = math.ceil(numerator / max(denominator, 1)) * (coding_rate + 4)
    n_payload = 8 + max(payload_symbols_term, 0)
    return (preamble_symbols + 4.25 + n_payload) * t_sym


def outage_ratio(outage_events: int, total_events: int) -> float:
    """Taux d'outage.

    Formule explicite: ``outage = outage_events / total_events``.
    """

    return float(outage_events) / _safe_denominator(float(total_events))
