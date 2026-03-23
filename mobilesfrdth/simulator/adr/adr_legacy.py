"""ADR legacy simplifié basé marge SNR."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdrLegacyConfig:
    target_margin_db: float = 10.0
    min_sf: int = 7
    max_sf: int = 12


def recommend_sf(current_sf: int, snr_db: float, cfg: AdrLegacyConfig) -> int:
    """Ajuste le SF via une marge SNR crédible et simple."""

    new_sf, _ = recommend_sf_with_reason(current_sf=current_sf, snr_db=snr_db, cfg=cfg)
    return new_sf


def recommend_sf_with_reason(current_sf: int, snr_db: float, cfg: AdrLegacyConfig) -> tuple[int, str]:
    """Ajuste le SF et renvoie la justification de décision."""

    new_sf = current_sf
    reason = "margin_stable"
    if snr_db > cfg.target_margin_db + 3.0:
        new_sf -= 1
        reason = "margin_high"
    elif snr_db < cfg.target_margin_db - 3.0:
        new_sf += 1
        reason = "margin_low"

    bounded_sf = max(cfg.min_sf, min(cfg.max_sf, new_sf))
    margin_db = snr_db - cfg.target_margin_db
    details = f"margin={margin_db:.2f}dB|airtime_cost=na|qos=na|rule={reason}"
    return bounded_sf, details
