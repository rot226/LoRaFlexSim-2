import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from mobilesfrdth.simulator.metrics import convergence_tc_performance


def test_convergence_tc_performance_uses_joint_pdr_der_threshold():
    pdr_series = [0.1, 0.3, 0.6, 0.8, 0.9]
    der_series = [0.05, 0.15, 0.2, 0.5, 0.9]

    tc_s = convergence_tc_performance(
        pdr_samples=pdr_series,
        der_samples=der_series,
        dt_s=10.0,
        moving_window_bins=1,
        stationary_tail_bins=2,
        target_ratio=0.9,
    )

    assert tc_s == 40.0


def test_convergence_tc_performance_returns_inf_if_one_metric_never_converges():
    tc_s = convergence_tc_performance(
        pdr_samples=[0.9, 0.95, 1.0],
        der_samples=[0.0, 0.0, 0.0],
        dt_s=5.0,
        moving_window_bins=1,
        stationary_tail_bins=2,
        target_ratio=1.1,
    )

    assert math.isinf(tc_s)
