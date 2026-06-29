from __future__ import annotations

from mobilesfrdth.jamming.metrics import compute_packet_metrics


def test_two_receptions_with_same_packet_id_do_not_double_count_pdr() -> None:
    metrics = compute_packet_metrics(
        [
            {"traffic_type": "legitimate", "event_type": "tx", "packet_id": "pkt-1"},
            {"traffic_type": "legitimate", "event_type": "rx", "packet_id": "pkt-1", "gateway_id": "gw-1"},
            {"traffic_type": "legitimate", "event_type": "rx", "packet_id": "pkt-1", "gateway_id": "gw-2"},
        ]
    )

    assert metrics["tx_packets_total"] == 1
    assert metrics["rx_packets_total"] == 2
    assert metrics["rx_unique_packets_total"] == 1
    assert metrics["duplicate_packets_total"] == 1
    assert metrics["pdr_percent"] == 100.0
