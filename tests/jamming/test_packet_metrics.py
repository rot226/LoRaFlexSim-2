from __future__ import annotations

from mobilesfrdth.jamming.metrics import compute_packet_metrics


def test_compute_packet_metrics_counts_duplicate_reception_once_for_pdr() -> None:
    metrics = compute_packet_metrics(
        [
            {"traffic_type": "legitimate", "event_type": "tx", "packet_id": "pkt-1"},
            {"traffic_type": "legitimate", "event_type": "rx", "packet_id": "pkt-1", "gateway_id": "gw-1"},
            {"traffic_type": "legitimate", "event_type": "rx", "packet_id": "pkt-1", "gateway_id": "gw-2"},
            {"traffic_type": "jammer", "event_type": "tx", "packet_id": "jam-1", "jammer_id": "jammer-1"},
        ]
    )

    assert metrics["tx_packets_total"] == 1
    assert metrics["rx_packets_total"] == 2
    assert metrics["rx_unique_packets_total"] == 1
    assert metrics["duplicate_packets_total"] == 1
    assert metrics["pdr_percent"] == 100.0
    assert metrics["packet_loss_rate_percent"] == 0.0
