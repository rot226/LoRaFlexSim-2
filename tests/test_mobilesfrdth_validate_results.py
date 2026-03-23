import pathlib

from mobilesfrdth.qa.validate_results import validate_strict_plot_outputs


def _write_csv(path: pathlib.Path, header: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [",".join(header)]
    for row in rows:
        lines.append(",".join(str(item) for item in row))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_validate_strict_detects_multiple_anomalies(tmp_path: pathlib.Path) -> None:
    aggregates = tmp_path / "aggregates"
    _write_csv(
        aggregates / "metric_by_factor.csv",
        ["N", "algo", "mode", "pdr_mean", "der_mean", "throughput_bps_mean", "jain_fairness_mean", "airtime_total_s_mean", "switch_count_mean"],
        [
            [50, "adr", "snir_on", 0.9, 0.8, 1000, 0.99, 10.0, 2.0],
            [50, "ucb", "snir_on", 0.9, 0.8, 1000, 0.99, 10.0, 2.0],
        ],
    )
    _write_csv(
        aggregates / "convergence_tc.csv",
        ["algo", "speed", "Tc_s"],
        [["adr", 1, 42], ["ucb", 3, 42]],
    )
    _write_csv(
        aggregates / "sinr_cdf.csv",
        ["algo", "mode", "N", "speed", "mobility_model", "gateways", "sigma", "quantile", "sinr_db"],
        [
            ["adr", "snir_on", 50, 1, "rwp", 1, 6, 0.1, -12],
            ["adr", "snir_on", 50, 1, "rwp", 1, 6, 0.05, -11],
        ],
    )

    issues = validate_strict_plot_outputs(
        aggregates_dir=aggregates,
        figure_filters=[{"figure": "fig01.png", "generated": False, "num_points": 0}],
    )

    joined = "\n".join(issues)
    assert "quasi identiques" in joined
    assert "Variance quasi nulle" in joined
    assert "Tc_s est constant" in joined
    assert "CDF non monotone" in joined
    assert "Figure non générée" in joined


def test_validate_strict_ok_when_data_varies(tmp_path: pathlib.Path) -> None:
    aggregates = tmp_path / "aggregates"
    _write_csv(
        aggregates / "metric_by_factor.csv",
        ["N", "algo", "mode", "pdr_mean", "der_mean", "throughput_bps_mean", "jain_fairness_mean", "airtime_total_s_mean", "switch_count_mean"],
        [
            [50, "adr", "snir_on", 0.7, 0.6, 900, 0.91, 15.0, 3.0],
            [50, "ucb", "snir_on", 0.85, 0.8, 1200, 0.95, 11.0, 2.0],
            [100, "adr", "snir_on", 0.6, 0.55, 850, 0.88, 18.0, 4.0],
            [100, "ucb", "snir_on", 0.82, 0.77, 1180, 0.93, 12.0, 2.0],
        ],
    )
    _write_csv(
        aggregates / "convergence_tc.csv",
        ["algo", "speed", "Tc_s"],
        [["adr", 1, 40], ["ucb", 3, 60]],
    )
    _write_csv(
        aggregates / "sinr_cdf.csv",
        ["algo", "mode", "N", "speed", "mobility_model", "gateways", "sigma", "quantile", "sinr_db"],
        [
            ["adr", "snir_on", 50, 1, "rwp", 1, 6, 0.1, -14],
            ["adr", "snir_on", 50, 1, "rwp", 1, 6, 0.5, -8],
            ["adr", "snir_on", 50, 1, "rwp", 1, 6, 1.0, -2],
        ],
    )

    issues = validate_strict_plot_outputs(
        aggregates_dir=aggregates,
        figure_filters=[{"figure": "fig01.png", "generated": True, "num_points": 12}],
    )

    assert issues == []
