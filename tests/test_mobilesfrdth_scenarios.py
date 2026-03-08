from pathlib import Path

from mobilesfrdth.scenarios import generate_jobs


def test_generate_jobs_run_id_contains_all_grid_factors(tmp_path: Path) -> None:
    jobs = generate_jobs(
        config_path=Path("experiments/default.yaml"),
        output_root=tmp_path,
        grid={
            "N": [50],
            "model": ["RWP"],
            "mode": ["SNIR_ON"],
            "algo": ["ADR_MIXRA"],
            "speed": [3.0],
            "gateways": [2],
            "sigma_shadowing": [4.0],
            "reps": [1],
            "seed_base": [1234],
        },
    )

    run_id = jobs[0]["params"]["run_id"]
    assert (
        run_id
        == "n-50_model-rwp_mode-snir-on_algo-adr-mixra_speed-3_gateways-2_sigma-shadowing-4_rep-1_seed-1234"
    )
