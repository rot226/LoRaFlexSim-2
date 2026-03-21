from __future__ import annotations

from pretest_campagne.scenario_c import run_all


def _patch_run_all_startup(monkeypatch):
    monkeypatch.setattr(run_all, "_enforce_expected_campaign_branch", lambda *_: None)
    monkeypatch.setattr(run_all, "_remove_global_aggregation_artifacts", lambda *_: None)
    monkeypatch.setattr(run_all, "_read_campaign_state", lambda *_: None)
    monkeypatch.setattr(run_all, "_find_first_missing_rep", lambda *_args, **_kwargs: 1)
    monkeypatch.setattr(run_all, "_count_failed_runs", lambda *_: 0)
    monkeypatch.setattr(run_all, "_write_campaign_state", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(run_all, "_log_existing_key_csv_paths", lambda *_: None)
    monkeypatch.setattr(run_all, "_remove_done_flag", lambda *_: None)
    monkeypatch.setattr(run_all, "_build_step2_quality_summary", lambda *_: {"simulation_quality": "ok", "reasons": []})
    monkeypatch.setattr(run_all, "_missing_replications_by_size", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(run_all, "run_step1", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(run_all, "run_step2", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(run_all, "aggregate_results_by_size", lambda *_args, **_kwargs: {"global_row_count": 0})
    monkeypatch.setattr(run_all, "_assert_cumulative_sizes_nested", lambda *_: None)
    monkeypatch.setattr(run_all, "_assert_output_layout_compliant", lambda *_: None)
    monkeypatch.setattr(run_all, "_assert_cumulative_sizes", lambda *_: None)
    monkeypatch.setattr(run_all, "_assert_aggregation_contract_consistent", lambda *_: None)
    monkeypatch.setattr(run_all, "validate_results", lambda *_: 0)

def test_run_all_skip_step2_never_crashes_on_missing_optional_attrs(monkeypatch):
    _patch_run_all_startup(monkeypatch)
    run_all.main(["--skip-step2"])



def test_run_all_skip_step1_never_crashes_on_missing_optional_attrs(monkeypatch):
    _patch_run_all_startup(monkeypatch)
    run_all.main(["--skip-step1"])
