from app.services.anomaly import AnomalyDetector


def test_latency_spike_detected():
    d=AnomalyDetector(window=20,min_samples=5)
    for value in [100,102,98,101,99]: assert d.detect("api","latency",value) is None
    result=d.detect("api","latency",500)
    assert result and result.category=="latency_spike" and result.severity=="critical"
def test_healthy_signal_ignored():
    d=AnomalyDetector(min_samples=5)
    for value in [100,102,99,101,100,102]: result=d.detect("api","latency",value)
    assert result is None
