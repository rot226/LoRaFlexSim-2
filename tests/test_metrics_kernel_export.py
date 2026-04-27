from types import SimpleNamespace

from loraflexsim.scenarios.qos_cluster_bench import _compute_additional_metrics


def test_compute_additional_metrics_exposes_comparable_kernel() -> None:
    node = SimpleNamespace(
        id=1,
        sf=7,
        tx_attempted=4,
        rx_delivered=3,
        acks_received=2,
        ack_failures=1,
    )
    simulator = SimpleNamespace(
        current_time=10.0,
        nodes=[node],
        events_log=[],
        use_snir=False,
        multichannel=None,
        channel=None,
        qos_clusters_config={},
        qos_node_clusters={},
        qos_mixra_solver=None,
    )
    metrics = {
        "PDR": 0.75,
        "throughput_bps": 128.0,
        "tx_attempted": 4,
        "delivered": 3,
        "energy_J": 6.0,
        "ack_success_count": 2,
        "ack_nack_count": 1,
        "sf_distribution": {7: 1},
    }

    enriched = _compute_additional_metrics(simulator, metrics, "mixra_opt", "auto")

    assert enriched["pdr_global"] == 0.75
    assert enriched["throughput_global_bps"] == 128.0
    assert enriched["energy_per_delivered_packet_J"] == 2.0
    assert enriched["ack_success_rate"] == 2 / 3
    assert enriched["ack_nack_rate"] == 1 / 3
    assert enriched["metric_kernel"]["sf_distribution"] == {7: 1}
