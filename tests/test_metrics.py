from retrylab.metrics import Metrics


def test_metrics_count_requests_faults_and_latency():
    metrics = Metrics()
    metrics.record(status_code=200, fault="none", duration_ms=10)
    metrics.record(status_code=503, fault="server_error", duration_ms=30)
    snapshot = metrics.snapshot()
    assert snapshot["requests_total"] == 2
    assert snapshot["responses_by_status"] == {"200": 1, "503": 1}
    assert snapshot["injected_faults"] == {"server_error": 1}
    assert snapshot["latency_ms"]["mean"] == 20
    assert snapshot["latency_ms"]["p50"] == 10


def test_empty_metrics_have_safe_zero_values():
    snapshot = Metrics().snapshot()
    assert snapshot["requests_total"] == 0
    assert snapshot["latency_ms"]["p95"] == 0
