import csv
import pathlib
import warnings
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from mobilesfrdth.plotting import plots
from mobilesfrdth.simulator.io import SUMMARY_COLUMNS, aggregate_runs


def _write_csv(path: pathlib.Path, headers: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})


def _summary_row(run_id: str, *, algo: str, pdr: float) -> dict[str, object]:
    return {
        "N": "50",
        "speed": "1",
        "mobility_model": "rwp",
        "mode": "snir_on",
        "algo": algo,
        "gateways": "1",
        "sigma": "2",
        "seed": "1",
        "rep": "0",
        "run_id": run_id,
        "duration_s": "100",
        "node_count": "50",
        "tx_count": "10",
        "success_count": "9",
        "generated_packets": "10",
        "delivered_bytes": "450",
        "pdr": str(pdr),
        "der": "0.9",
        "throughput_bps": "36",
        "Tc_s": "25",
        "jain_fairness": "0.95",
        "airtime_total_s": "12.5",
        "airtime_mean_per_node_s": "0.25",
        "outage_ratio": "0.1",
        "switch_count": "3",
    }


def test_metric_by_factor_is_aggregated_per_algo(tmp_path):
    run_a = tmp_path / "results" / "run_adr"
    run_b = tmp_path / "results" / "run_ucb"
    _write_csv(run_a / "summary.csv", SUMMARY_COLUMNS, [_summary_row("run_adr", algo="adr", pdr=0.1)])
    _write_csv(run_b / "summary.csv", SUMMARY_COLUMNS, [_summary_row("run_ucb", algo="ucb", pdr=0.8)])

    files = aggregate_runs(inputs=[tmp_path], output_root=tmp_path / "out", summary_only=True)

    with files["metric_by_factor"].open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 2
    by_algo = {row["algo"]: row for row in rows}
    assert set(by_algo) == {"adr", "ucb"}
    assert by_algo["adr"]["pdr_mean"] == "0.1"
    assert by_algo["ucb"]["pdr_mean"] == "0.8"




def test_metric_by_factor_uses_full_factor_key_with_model_and_sigma_shadowing_aliases(tmp_path):
    run_dir_a = tmp_path / "results" / "run_adr"
    run_dir_b = tmp_path / "results" / "run_ucb"

    headers = [
        "N",
        "speed",
        "model",
        "mode",
        "algo",
        "gateways",
        "sigma_shadowing",
        "seed",
        "rep",
        "run_id",
        "pdr",
        "der",
        "throughput_bps",
        "Tc_s",
        "jain_fairness",
        "airtime_total_s",
        "outage_ratio",
        "switch_count",
    ]

    rows = [
        {
            "N": "50",
            "speed": "1",
            "model": "rwp",
            "mode": "snir_on",
            "algo": "adr",
            "gateways": "1",
            "sigma_shadowing": "2",
            "seed": "1",
            "rep": "0",
            "run_id": "run_adr",
            "pdr": "0.11",
            "der": "0.11",
            "throughput_bps": "10",
            "Tc_s": "10",
            "jain_fairness": "0.8",
            "airtime_total_s": "1",
            "outage_ratio": "0.2",
            "switch_count": "1",
        },
        {
            "N": "50",
            "speed": "1",
            "model": "rwp",
            "mode": "snir_on",
            "algo": "ucb",
            "gateways": "1",
            "sigma_shadowing": "2",
            "seed": "1",
            "rep": "0",
            "run_id": "run_ucb",
            "pdr": "0.77",
            "der": "0.77",
            "throughput_bps": "10",
            "Tc_s": "10",
            "jain_fairness": "0.8",
            "airtime_total_s": "1",
            "outage_ratio": "0.2",
            "switch_count": "1",
        },
    ]

    _write_csv(run_dir_a / "summary.csv", headers, [rows[0]])
    _write_csv(run_dir_b / "summary.csv", headers, [rows[1]])

    files = aggregate_runs(inputs=[tmp_path], output_root=tmp_path / "out", summary_only=True)

    with files["metric_by_factor"].open("r", encoding="utf-8", newline="") as handle:
        aggregated = list(csv.DictReader(handle))

    assert len(aggregated) == 2
    by_algo = {row["algo"]: row for row in aggregated}
    assert by_algo["adr"]["mobility_model"] == "rwp"
    assert by_algo["adr"]["sigma"] == "2"
    assert by_algo["adr"]["pdr_mean"] == "0.11"
    assert by_algo["ucb"]["pdr_mean"] == "0.77"

def test_plot_xy_by_algo_uses_distinct_series_per_algo(monkeypatch, tmp_path):
    rows = [
        {"N": "50", "algo": "adr", "pdr_mean": "0.10"},
        {"N": "100", "algo": "adr", "pdr_mean": "0.12"},
        {"N": "50", "algo": "adr_mixra", "pdr_mean": "0.20"},
        {"N": "100", "algo": "adr_mixra", "pdr_mean": "0.22"},
        {"N": "50", "algo": "ucb", "pdr_mean": "0.30"},
        {"N": "100", "algo": "ucb", "pdr_mean": "0.32"},
        {"N": "50", "algo": "ucb_forget", "pdr_mean": "0.40"},
        {"N": "100", "algo": "ucb_forget", "pdr_mean": "0.42"},
    ]

    captured: list[dict[str, object]] = []

    def fake_plot(xs, ys, *args, **kwargs):
        captured.append({"label": kwargs.get("label"), "xs": tuple(xs), "ys": tuple(ys)})
        return []

    monkeypatch.setattr(plots.plt, "errorbar", fake_plot)
    monkeypatch.setattr(plots.plt, "legend", lambda *args, **kwargs: None)

    out_path = tmp_path / "fig01_pdr_vs_n_snir_off.png"
    generated = plots._plot_xy_by_algo(rows, fig_name=out_path.name, y_col="pdr_mean", out_path=out_path)

    assert generated is True
    assert len(captured) == 4

    curves = {item["label"]: item["ys"] for item in captured}
    assert set(curves) == {"adr", "adr_mixra", "ucb", "ucb_forget"}
    assert len(set(curves.values())) == 4


def test_plot_sinr_cdf_single_curve_per_algo_sorted_quantiles(monkeypatch, tmp_path):
    rows = [
        {"algo": "adr", "mode": "snir_on", "N": "50", "speed": "1", "quantile": "0.5", "sinr_db": "4.0"},
        {"algo": "adr", "mode": "snir_on", "N": "50", "speed": "1", "quantile": "0.0", "sinr_db": "1.0"},
        {"algo": "adr", "mode": "snir_on", "N": "50", "speed": "1", "quantile": "1.0", "sinr_db": "8.0"},
        {"algo": "ucb", "mode": "snir_on", "N": "50", "speed": "1", "quantile": "0.5", "sinr_db": "5.0"},
        {"algo": "ucb", "mode": "snir_on", "N": "50", "speed": "1", "quantile": "0.0", "sinr_db": "2.0"},
        {"algo": "ucb", "mode": "snir_on", "N": "50", "speed": "1", "quantile": "1.0", "sinr_db": "9.0"},
    ]

    captured: list[dict[str, object]] = []

    def fake_plot(xs, ys, *args, **kwargs):
        captured.append({"label": kwargs.get("label"), "xs": tuple(xs), "ys": tuple(ys)})
        return []

    monkeypatch.setattr(plots.plt, "plot", fake_plot)
    monkeypatch.setattr(plots.plt, "legend", lambda *args, **kwargs: None)

    out_path = tmp_path / "fig10_sinr_cdf.png"
    generated = plots._plot_sinr_cdf(rows, out_path)

    assert generated is True
    assert len(captured) == 2
    by_algo = {item["label"]: item for item in captured}
    assert tuple(by_algo["adr"]["ys"]) == (0.0, 0.5, 1.0)
    assert tuple(by_algo["ucb"]["ys"]) == (0.0, 0.5, 1.0)


def test_plot_sinr_cdf_accepts_constant_sinr_group(tmp_path):
    rows = [
        {"algo": "adr", "mode": "snir_on", "N": "50", "speed": "1", "quantile": "0.0", "sinr_db": "3.0"},
        {"algo": "adr", "mode": "snir_on", "N": "50", "speed": "1", "quantile": "0.5", "sinr_db": "3.0"},
        {"algo": "adr", "mode": "snir_on", "N": "50", "speed": "1", "quantile": "1.0", "sinr_db": "3.0"},
    ]

    out_path = tmp_path / "fig10_sinr_cdf.png"
    generated = plots._plot_sinr_cdf(rows, out_path)

    assert generated is True

