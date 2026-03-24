"""Integration tests validating LoRaFlexSim against FLoRa baselines."""

from __future__ import annotations

from pathlib import Path

import pytest

try:  # pragma: no cover - optional dependency
    import pandas as _pd  # noqa: F401
except Exception:  # pragma: no cover - skip if pandas unusable
    pytest.skip("pandas is required for validation comparisons", allow_module_level=True)

from loraflexsim.launcher import adr_ml, explora_at
from loraflexsim.validation import (
    SCENARIOS,
    compare_to_reference,
    load_flora_reference,
    run_validation,
)

pytestmark = pytest.mark.slow

PDR_TOL_FLOOR = 0.35
COLLISION_TOL_FLOOR = 3.0
SNR_TOL_FLOOR = 7.0


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda sc: sc.name)
def test_scenario_matches_flora_reference(scenario):
    """Each validation scenario stays within the tolerance bound."""

    assert Path(scenario.flora_config).exists(), f"Missing FLoRa config {scenario.flora_config}"
    assert Path(scenario.flora_reference).exists(), f"Missing reference file {scenario.flora_reference}"

    sim = scenario.build_simulator()
    metrics = run_validation(sim, scenario.run_steps)
    reference = load_flora_reference(scenario.flora_reference)
    deltas = compare_to_reference(metrics, reference, scenario.tolerances)

    pdr_tol = max(scenario.tolerances.pdr, PDR_TOL_FLOOR)
    assert deltas["PDR"] <= pdr_tol, (
        f"PDR delta {deltas['PDR']:.3f} exceeds tolerance {pdr_tol:.3f}"
    )
    collisions_tol = max(float(scenario.tolerances.collisions), COLLISION_TOL_FLOOR)
    assert deltas["collisions"] <= collisions_tol, (
        f"Collision delta {deltas['collisions']:.3f} exceeds tolerance {collisions_tol:.3f}"
    )
    snr_tol = max(scenario.tolerances.snr, SNR_TOL_FLOOR)
    assert deltas["snr"] <= snr_tol, (
        f"SNR delta {deltas['snr']:.3f} exceeds tolerance {snr_tol:.3f}"
    )


def test_multi_gateway_adr_alignment_matches_flora():
    """Average SNIR from each gateway matches FLoRa for the multi-GW scenario."""

    scenario = next(
        sc for sc in SCENARIOS if sc.name == "multi_gw_multichannel_server_adr"
    )
    sim = scenario.build_simulator()
    run_validation(sim, scenario.run_steps)
    reference = load_flora_reference(scenario.flora_reference)

    ns = sim.network_server
    snir_samples: list[float] = []
    for per_event in ns.gateway_snr_samples.values():
        snir_samples.extend(per_event.values())

    assert snir_samples, "No SNIR samples recorded for gateways"
    avg_snir = sum(snir_samples) / len(snir_samples)
    snr_tol = max(scenario.tolerances.snr, 2.5)
    assert avg_snir == pytest.approx(
        reference["snr"], abs=snr_tol
    )


def test_validation_matrix_covers_specialised_modules():
    """Each advanced module is represented by at least one scenario."""

    def _has(predicate):
        return any(predicate(sc) for sc in SCENARIOS)

    assert _has(
        lambda sc: sc.sim_kwargs.get("duty_cycle") not in (None, 0)
    ), "Duty-cycle scenario missing"
    assert _has(
        lambda sc: sc.sim_kwargs.get("channel_distribution") == "random"
    ), "Dynamic multichannel scenario missing"
    assert _has(
        lambda sc: sc.sim_kwargs.get("node_class") == "B"
        and (
            sc.sim_kwargs.get("mobility")
            or sc.sim_kwargs.get("mobility_model") is not None
        )
    ), "Class B mobility scenario missing"
    assert _has(
        lambda sc: sc.sim_kwargs.get("node_class") == "C"
        and (
            sc.sim_kwargs.get("mobility")
            or sc.sim_kwargs.get("mobility_model") is not None
        )
    ), "Class C mobility scenario missing"
    assert _has(
        lambda sc: any(hook is explora_at.apply for hook in getattr(sc, "setup", ()))
    ), "EXPLoRa scenario missing"
    assert _has(
        lambda sc: any(hook is adr_ml.apply for hook in getattr(sc, "setup", ()))
    ), "ADR-ML scenario missing"
