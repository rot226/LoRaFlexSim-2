#!/usr/bin/env python3
"""Calibration rapide SNIR_ON/SNIR_OFF: tendance PDR/DER vs densité N."""

from __future__ import annotations

from dataclasses import dataclass
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mobilesfrdth.simulator.channel import ChannelConfig, received_power_dbm
from mobilesfrdth.simulator.interference import InterferenceConfig, transmission_success


@dataclass(frozen=True)
class TrendPoint:
    n: int
    pdr_off: float
    der_off: float
    pdr_on: float
    der_on: float


def _scenario_metrics(node_count: int, *, snir_enabled: bool) -> tuple[float, float]:
    channel_cfg = ChannelConfig(
        pathloss_exponent=2.95,
        sigma_shadowing=0.0,
        rayleigh_fading=False,
    )
    interference_cfg = InterferenceConfig(snir_enabled=snir_enabled)

    distances_m = [170.0 + (idx % 30) * 40.0 + (idx // 30) * 30.0 for idx in range(node_count)]
    spreading_factors = [7 + (idx % 6) for idx in range(node_count)]
    rx_powers_dbm = [
        received_power_dbm(tx_power_dbm=14.0, distance_m=distance_m, cfg=channel_cfg)
        for distance_m in distances_m
    ]

    delivered = 0
    for idx in range(node_count):
        interferers = [(rx_powers_dbm[j], spreading_factors[j]) for j in range(node_count) if j != idx]
        success, _ = transmission_success(
            rx_powers_dbm[idx],
            signal_sf=spreading_factors[idx],
            interferers=interferers,
            cfg=interference_cfg,
        )
        delivered += int(success)

    pdr = delivered / max(node_count, 1)
    der = pdr
    return pdr, der


def _trend_points() -> list[TrendPoint]:
    points: list[TrendPoint] = []
    for n in (40, 80, 120, 180, 240):
        pdr_off, der_off = _scenario_metrics(n, snir_enabled=False)
        pdr_on, der_on = _scenario_metrics(n, snir_enabled=True)
        points.append(TrendPoint(n=n, pdr_off=pdr_off, der_off=der_off, pdr_on=pdr_on, der_on=der_on))
    return points


def _fmt(x: float) -> str:
    return f"{x:.3f}"


def main() -> int:
    points = _trend_points()

    print("Calibration simple SNIR: tendances attendues")
    print("N\tPDR_OFF\tPDR_ON\tDER_OFF\tDER_ON\tΔPDR(ON-OFF)")
    for point in points:
        print(
            f"{point.n}\t{_fmt(point.pdr_off)}\t{_fmt(point.pdr_on)}\t"
            f"{_fmt(point.der_off)}\t{_fmt(point.der_on)}\t{_fmt(point.pdr_on - point.pdr_off)}"
        )

    pdr_on_monotonic_drop = all(points[i + 1].pdr_on <= points[i].pdr_on for i in range(len(points) - 1))
    der_on_monotonic_drop = all(points[i + 1].der_on <= points[i].der_on for i in range(len(points) - 1))
    snir_on_worse_high_load = points[-1].pdr_on < points[-1].pdr_off and points[-1].der_on < points[-1].der_off

    print()
    print(f"Check N↑ => PDR↓ (SNIR_ON): {'OK' if pdr_on_monotonic_drop else 'KO'}")
    print(f"Check N↑ => DER↓ (SNIR_ON): {'OK' if der_on_monotonic_drop else 'KO'}")
    print(f"Check charge élevée: SNIR_ON < SNIR_OFF (PDR/DER): {'OK' if snir_on_worse_high_load else 'KO'}")

    if pdr_on_monotonic_drop and der_on_monotonic_drop and snir_on_worse_high_load:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
