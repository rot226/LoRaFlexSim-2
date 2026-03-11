"""Couplage ADR (SF) + MixRA (puissance)."""

from __future__ import annotations

from dataclasses import dataclass

from .adr_legacy import AdrLegacyConfig, recommend_sf_with_reason
from .mixra import MixRaConfig, adjust_tx_power


@dataclass(frozen=True)
class AdrMixRaConfig:
    adr: AdrLegacyConfig = AdrLegacyConfig()
    mixra: MixRaConfig = MixRaConfig()


def adapt_link(
    *,
    current_sf: int,
    current_tx_power_dbm: float,
    snr_db: float,
    pdr_estimate: float,
    latency_estimate_s: float,
    cfg: AdrMixRaConfig,
) -> tuple[int, float, str]:
    """Retourne ``(sf, tx_power_dbm, reason)`` après adaptation conjointe."""

    sf, adr_reason = recommend_sf_with_reason(current_sf=current_sf, snr_db=snr_db, cfg=cfg.adr)

    qos_status = "ok"
    sf_rule = "sf_keep"
    if pdr_estimate < cfg.mixra.pdr_target:
        sf = min(cfg.adr.max_sf, sf + 1)
        qos_status = "degraded"
        sf_rule = "qos_reliability_boost"
    elif latency_estimate_s > cfg.mixra.latency_target_s or snr_db > (cfg.adr.target_margin_db + 1.0):
        sf = max(cfg.adr.min_sf, sf - 1)
        sf_rule = "airtime_reduce"

    tx = adjust_tx_power(
        current_tx_power_dbm=current_tx_power_dbm,
        pdr_estimate=pdr_estimate,
        latency_estimate_s=latency_estimate_s,
        cfg=cfg.mixra,
    )
    reason = (
        f"{adr_reason}|airtime_cost={latency_estimate_s:.3f}s|"
        f"qos={qos_status}|sf_rule={sf_rule}"
    )
    return sf, tx, reason
