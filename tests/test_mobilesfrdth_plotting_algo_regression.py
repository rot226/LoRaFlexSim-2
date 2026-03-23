import csv
import pathlib
import warnings

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
        "sigma_shadowing": "2",
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
    assert by_algo["adr"]["sigma_shadowing"] == "2"
    assert by_algo["adr"]["pdr_mean"] == "0.11"
    assert by_algo["ucb"]["pdr_mean"] == "0.77"



def test_metric_by_factor_exposes_sigma_shadowing_column(tmp_path):
    run_a = tmp_path / "results" / "run_adr"
    run_b = tmp_path / "results" / "run_ucb"
    _write_csv(run_a / "summary.csv", SUMMARY_COLUMNS, [_summary_row("run_adr", algo="adr", pdr=0.1)])
    _write_csv(run_b / "summary.csv", SUMMARY_COLUMNS, [_summary_row("run_ucb", algo="ucb", pdr=0.8)])

    files = aggregate_runs(inputs=[tmp_path], output_root=tmp_path / "out", summary_only=True)

    with files["metric_by_factor"].open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert "sigma_shadowing" in rows[0]
    assert rows[0]["sigma_shadowing"] == "2"


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
        {"N": "50", "algo": "", "pdr_mean": "0.99"},
    ]

    captured: list[dict[str, object]] = []

    def fake_plot(xs, ys, *args, **kwargs):
        captured.append({"label": kwargs.get("label"), "xs": tuple(xs), "ys": tuple(ys)})
        return []

    monkeypatch.setattr(plots.plt, "plot", fake_plot)
    monkeypatch.setattr(plots.plt, "errorbar", fake_plot)
    monkeypatch.setattr(plots.plt, "fill_between", lambda *args, **kwargs: [])
    monkeypatch.setattr(plots.plt, "legend", lambda *args, **kwargs: None)

    out_path = tmp_path / "fig01_pdr_vs_n_snir_off.png"
    generated = plots._plot_xy_by_algo(rows, fig_name=out_path.name, y_col="pdr_mean", out_path=out_path)

    assert generated is True
    assert len(captured) == 8

    curves = {item["label"]: item["ys"] for item in captured if item["label"] is not None}
    assert set(curves) == {"adr", "adr_mixra", "ucb", "ucb_forget"}
    assert "" not in curves
    assert len(set(curves.values())) == 4


def test_plot_xy_by_algo_uses_csv_ci_band_when_available(monkeypatch, tmp_path):
    rows = [
        {
            "N": "50",
            "algo": "adr",
            "pdr_mean": "0.90",
            "pdr_ci95": "0.02",
            "pdr_ci95_low": "0.88",
            "pdr_ci95_high": "0.92",
        },
        {
            "N": "100",
            "algo": "adr",
            "pdr_mean": "0.85",
            "pdr_ci95": "0.01",
            "pdr_ci95_low": "0.84",
            "pdr_ci95_high": "0.86",
        },
    ]

    fill_calls: list[tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...]]] = []
    err_calls: list[tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...]]] = []

    monkeypatch.setattr(plots.plt, "plot", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        plots.plt,
        "fill_between",
        lambda xs, lows, highs, *args, **kwargs: fill_calls.append((tuple(xs), tuple(lows), tuple(highs))),
    )
    monkeypatch.setattr(
        plots.plt,
        "errorbar",
        lambda xs, ys, *args, **kwargs: err_calls.append((tuple(xs), tuple(ys), tuple(kwargs.get("yerr", [])))),
    )
    monkeypatch.setattr(plots.plt, "legend", lambda *args, **kwargs: None)

    out_path = tmp_path / "fig01_pdr_vs_n_snir_off.png"
    generated = plots._plot_xy_by_algo(rows, fig_name=out_path.name, y_col="pdr_mean", out_path=out_path)

    assert generated is True
    assert len(fill_calls) == 1
    assert fill_calls[0] == ((50.0, 100.0), (0.88, 0.84), (0.92, 0.86))
    assert len(err_calls) == 1
    assert err_calls[0][2] == (0.020000000000000018, 0.010000000000000009)


def test_plot_xy_by_algo_auto_adds_annex_for_reliability_close_to_one(monkeypatch, tmp_path):
    rows = [
        {"N": "50", "algo": "adr", "pdr_mean": "0.97"},
        {"N": "100", "algo": "adr", "pdr_mean": "0.98"},
    ]

    saved: list[pathlib.Path] = []

    def fake_save(path: pathlib.Path) -> None:
        saved.append(path)

    monkeypatch.setattr(plots, "_save_figure_variants", fake_save)
    monkeypatch.setattr(plots.plt, "legend", lambda *args, **kwargs: None)

    out_path = tmp_path / "fig01_pdr_vs_n_snir_on.png"
    generated = plots._plot_xy_by_algo(rows, fig_name=out_path.name, y_col="pdr_mean", out_path=out_path, y_scale="auto")

    assert generated is True
    assert out_path in saved
    assert out_path.with_name("fig01_pdr_vs_n_snir_on_annex_full_scale.png") in saved


def test_plot_xy_by_algo_full_scale_no_annex(monkeypatch, tmp_path):
    rows = [
        {"N": "50", "algo": "adr", "der_mean": "0.96"},
        {"N": "100", "algo": "adr", "der_mean": "0.99"},
    ]

    saved: list[pathlib.Path] = []

    monkeypatch.setattr(plots, "_save_figure_variants", lambda path: saved.append(path))
    monkeypatch.setattr(plots.plt, "legend", lambda *args, **kwargs: None)

    out_path = tmp_path / "fig03_der_vs_n_snir_off.png"
    generated = plots._plot_xy_by_algo(rows, fig_name=out_path.name, y_col="der_mean", out_path=out_path, y_scale="full")

    assert generated is True
    assert saved == [out_path]


def test_plot_sinr_cdf_single_curve_per_algo_sorted_quantiles(monkeypatch, tmp_path):
    rows = [
        {"algo": "adr", "mode": "snir_on", "N": "50", "speed": "1", "mobility_model": "rwp", "gateways": "1", "sigma_shadowing": "2", "quantile": "0.666667", "sinr_db": "4.0"},
        {"algo": "adr", "mode": "snir_on", "N": "50", "speed": "1", "mobility_model": "rwp", "gateways": "1", "sigma_shadowing": "2", "quantile": "0.333333", "sinr_db": "1.0"},
        {"algo": "adr", "mode": "snir_on", "N": "50", "speed": "1", "mobility_model": "rwp", "gateways": "1", "sigma_shadowing": "2", "quantile": "1.0", "sinr_db": "8.0"},
        {"algo": "ucb", "mode": "snir_on", "N": "50", "speed": "1", "mobility_model": "rwp", "gateways": "1", "sigma_shadowing": "2", "quantile": "0.666667", "sinr_db": "5.0"},
        {"algo": "ucb", "mode": "snir_on", "N": "50", "speed": "1", "mobility_model": "rwp", "gateways": "1", "sigma_shadowing": "2", "quantile": "0.333333", "sinr_db": "2.0"},
        {"algo": "ucb", "mode": "snir_on", "N": "50", "speed": "1", "mobility_model": "rwp", "gateways": "1", "sigma_shadowing": "2", "quantile": "1.0", "sinr_db": "9.0"},
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
    by_label = {item["label"]: item for item in captured}
    assert tuple(by_label["adr"]["ys"]) == (0.333333, 0.666667, 1.0)
    assert tuple(by_label["ucb"]["ys"]) == (0.333333, 0.666667, 1.0)


def test_plot_sinr_cdf_rejects_constant_sinr_group(tmp_path):
    rows = [
        {"algo": "adr", "mode": "snir_on", "N": "50", "speed": "1", "mobility_model": "rwp", "gateways": "1", "sigma_shadowing": "2", "quantile": "0.333333", "sinr_db": "3.0"},
        {"algo": "adr", "mode": "snir_on", "N": "50", "speed": "1", "mobility_model": "rwp", "gateways": "1", "sigma_shadowing": "2", "quantile": "0.666667", "sinr_db": "3.0"},
        {"algo": "adr", "mode": "snir_on", "N": "50", "speed": "1", "mobility_model": "rwp", "gateways": "1", "sigma_shadowing": "2", "quantile": "1.0", "sinr_db": "3.0"},
    ]

    out_path = tmp_path / "fig10_sinr_cdf.png"
    generated = plots._plot_sinr_cdf(rows, out_path)

    assert generated is False


def test_plot_fig14_pareto_reliability_airtime_uses_dedicated_aggregate(monkeypatch, tmp_path):
    rows = [
        {"algo": "ucb", "pdr_mean": "0.8", "pdr_ci95": "0.02", "airtime_total_s_mean": "11", "airtime_total_s_ci95": "1.1"},
        {"algo": "ucb", "pdr_mean": "0.82", "pdr_ci95": "0.03", "airtime_total_s_mean": "10", "airtime_total_s_ci95": "1.0"},
        {"algo": "adr", "pdr_mean": "0.7", "pdr_ci95": "0.04", "airtime_total_s_mean": "9", "airtime_total_s_ci95": "0.7"},
        {"algo": "adr", "pdr_mean": "0.72", "pdr_ci95": "0.05", "airtime_total_s_mean": "8", "airtime_total_s_ci95": "0.6"},
    ]

    monkeypatch.setattr(plots.plt, "legend", lambda *args, **kwargs: None)
    out_path = tmp_path / "fig14_pareto_reliability_airtime.png"
    assert plots._plot_airtime_reliability_pareto(rows, out_path) is True


def test_plot_fig15_outage_probability_vs_n_uses_dedicated_aggregate(monkeypatch, tmp_path):
    rows = [
        {"algo": "adr", "N": "50", "outage_prob_mean": "0.15", "outage_prob_ci95": "0.02"},
        {"algo": "adr", "N": "100", "outage_prob_mean": "0.2", "outage_prob_ci95": "0.03"},
        {"algo": "ucb", "N": "50", "outage_prob_mean": "0.1", "outage_prob_ci95": "0.01"},
        {"algo": "ucb", "N": "100", "outage_prob_mean": "0.13", "outage_prob_ci95": "0.02"},
    ]

    monkeypatch.setattr(plots.plt, "legend", lambda *args, **kwargs: None)
    out_path = tmp_path / "fig15_outage_probability_vs_n.png"
    assert plots._plot_outage_probability_vs_n(rows, out_path) is True


def test_plot_fig16_energy_efficiency_vs_reliability_uses_dedicated_aggregate(monkeypatch, tmp_path):
    rows = [
        {"algo": "adr", "pdr_mean": "0.70", "pdr_ci95": "0.03", "energy_efficiency_mean": "2.2", "energy_efficiency_ci95": "0.2"},
        {"algo": "adr", "pdr_mean": "0.72", "pdr_ci95": "0.02", "energy_efficiency_mean": "2.1", "energy_efficiency_ci95": "0.1"},
        {"algo": "ucb", "pdr_mean": "0.80", "pdr_ci95": "0.02", "energy_efficiency_mean": "2.4", "energy_efficiency_ci95": "0.2"},
        {"algo": "ucb", "pdr_mean": "0.81", "pdr_ci95": "0.02", "energy_efficiency_mean": "2.5", "energy_efficiency_ci95": "0.2"},
    ]

    monkeypatch.setattr(plots.plt, "legend", lambda *args, **kwargs: None)
    out_path = tmp_path / "fig16_energy_efficiency_vs_reliability.png"
    assert plots._plot_energy_efficiency_vs_reliability(rows, out_path) is True


def test_validate_curve_grouping_rejects_mixed_contexts_for_single_curve() -> None:
    rows = [
        {
            "algo": "adr",
            "mode": "snir_off",
            "N": "50",
            "speed": "1",
            "mobility_model": "rwp",
            "gateways": "1",
            "sigma_shadowing": "2",
            "pdr_mean": "0.8",
        },
        {
            "algo": "adr",
            "mode": "snir_off",
            "N": "100",
            "speed": "1",
            "mobility_model": "rwp",
            "gateways": "1",
            "sigma_shadowing": "2",
            "pdr_mean": "0.82",
        },
        {
            "algo": "adr",
            "mode": "snir_off",
            "N": "50",
            "speed": "3",
            "mobility_model": "rwp",
            "gateways": "1",
            "sigma_shadowing": "2",
            "pdr_mean": "0.79",
        },
    ]

    ok, summary = plots._validate_curve_grouping_or_skip(
        rows,
        figure="fig01_pdr_vs_n_snir_off.png",
        curve_column="algo",
        varying_columns={"N"},
    )

    assert ok is False
    assert summary["mixed_curves"] == ["adr"]


def test_generate_minimal_figures_writes_grouping_summary_and_skips_mixed_curve(tmp_path) -> None:
    aggregates_dir = tmp_path / "aggregates"
    figures_dir = tmp_path / "figures"
    aggregates_dir.mkdir(parents=True, exist_ok=True)

    metric_headers = [
        "N",
        "algo",
        "mode",
        "speed",
        "mobility_model",
        "gateways",
        "sigma_shadowing",
        "pdr_mean",
        "der_mean",
        "throughput_bps_mean",
        "jain_fairness_mean",
        "airtime_total_s_mean",
        "switch_count_mean",
    ]
    metric_rows = [
        {
            "N": "50",
            "algo": "adr",
            "mode": "snir_off",
            "speed": "1",
            "mobility_model": "rwp",
            "gateways": "1",
            "sigma_shadowing": "2",
            "pdr_mean": "0.80",
            "der_mean": "0.75",
            "throughput_bps_mean": "1000",
            "jain_fairness_mean": "0.91",
            "airtime_total_s_mean": "10",
            "switch_count_mean": "2",
        },
        {
            "N": "100",
            "algo": "adr",
            "mode": "snir_off",
            "speed": "3",
            "mobility_model": "rwp",
            "gateways": "1",
            "sigma_shadowing": "2",
            "pdr_mean": "0.78",
            "der_mean": "0.73",
            "throughput_bps_mean": "980",
            "jain_fairness_mean": "0.90",
            "airtime_total_s_mean": "11",
            "switch_count_mean": "2",
        },
    ]
    _write_csv(aggregates_dir / "metric_by_factor.csv", metric_headers, metric_rows)
    _write_csv(aggregates_dir / "distribution_sf.csv", ["algo", "sf", "ratio"], [{"algo": "adr", "sf": "7", "ratio": "1.0"}])

    _, traces = plots.generate_minimal_figures(
        aggregates_dir=aggregates_dir,
        out_dir=figures_dir,
        filters=plots.ScenarioFilters.from_tokens([]),
        include_bonus=False,
    )

    by_figure = {trace.figure: trace for trace in traces}
    assert by_figure["fig01_pdr_vs_n_snir_off.png"].generated is False
    assert by_figure["fig01_pdr_vs_n_snir_off.png"].grouping_summary["mixed_curves"] == ["adr"]

    import json

    payload = json.loads((figures_dir / "plots_summary.json").read_text(encoding="utf-8"))
    fig01 = next(item for item in payload["figures"] if item["figure"] == "fig01_pdr_vs_n_snir_off.png")
    assert fig01["grouping"]["mixed_curves"] == ["adr"]


def test_plot_xy_by_algo_applies_algo_style_colors(monkeypatch, tmp_path):
    import matplotlib.colors as mcolors

    rows = [
        {"N": "50", "algo": "adr", "pdr_mean": "0.10"},
        {"N": "100", "algo": "adr", "pdr_mean": "0.12"},
        {"N": "50", "algo": "ucb", "pdr_mean": "0.30"},
        {"N": "100", "algo": "ucb", "pdr_mean": "0.32"},
    ]

    captured_figs = []
    monkeypatch.setattr(plots, "_save_figure_variants", lambda path: None)
    monkeypatch.setattr(plots.plt, "close", lambda fig=None: captured_figs.append(plots.plt.gcf()))

    out_path = tmp_path / "fig01_pdr_vs_n_snir_off.png"
    assert plots._plot_xy_by_algo(rows, fig_name=out_path.name, y_col="pdr_mean", out_path=out_path) is True

    assert captured_figs
    ax = captured_figs[0].axes[0]
    container_by_algo = {container.get_label(): container for container in ax.containers if hasattr(container, "lines")}
    assert mcolors.to_hex(container_by_algo["adr"].lines[0].get_color()) == mcolors.to_hex(plots.ALGO_STYLE["adr"].color)
    assert mcolors.to_hex(container_by_algo["ucb"].lines[0].get_color()) == mcolors.to_hex(plots.ALGO_STYLE["ucb"].color)


def test_plot_sf_distribution_small_multiples_applies_algo_color_per_subplot(monkeypatch, tmp_path):
    import matplotlib.colors as mcolors

    rows = [
        {"algo": "adr", "sf": "7", "ratio": "0.4"},
        {"algo": "adr", "sf": "8", "ratio": "0.6"},
        {"algo": "ucb", "sf": "7", "ratio": "0.2"},
        {"algo": "ucb", "sf": "8", "ratio": "0.8"},
    ]

    captured_figs = []
    monkeypatch.setattr(plots.plt, "close", lambda fig=None: captured_figs.append(fig if fig is not None else plots.plt.gcf()))

    out_path = tmp_path / "fig09b_sf_distribution_snir_on_small_multiples.png"
    assert plots._plot_sf_distribution_small_multiples(rows, out_path) is True

    assert captured_figs
    fig = captured_figs[0]
    axes = fig.axes
    algo_names = [axis.get_legend().get_texts()[0].get_text() for axis in axes]
    for axis, algo in zip(axes, algo_names, strict=False):
        assert axis.patches
        first_patch_color = mcolors.to_hex(axis.patches[0].get_facecolor())
        assert first_patch_color == mcolors.to_hex(plots.ALGO_STYLE[algo].color)
