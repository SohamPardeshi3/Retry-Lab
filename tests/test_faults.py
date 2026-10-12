import pytest

from retrylab.faults import FaultScenario


def test_empty_header_means_no_fault():
    assert FaultScenario.from_header(None).kind == "none"
    assert FaultScenario.from_header("").kind == "none"


def test_latency_scenario_is_bounded():
    scenario = FaultScenario.from_header("latency:250")
    assert scenario.kind == "latency"
    assert scenario.delay_ms == 250


@pytest.mark.parametrize("header", ["latency:0", "latency:10001", "latency:nope", "unknown", "server_error:404", "timeout:999999"])
def test_invalid_scenarios_are_rejected(header):
    with pytest.raises(ValueError):
        FaultScenario.from_header(header)


def test_server_error_scenario():
    scenario = FaultScenario.from_header("server_error:503")
    assert scenario.kind == "server_error"
    assert scenario.status_code == 503


def test_rate_limit_scenario():
    scenario = FaultScenario.from_header("rate_limit")
    assert scenario.kind == "rate_limit"
    assert scenario.status_code == 429


@pytest.mark.asyncio
async def test_latency_sleeps_without_blocking_event_loop():
    scenario = FaultScenario.from_header("latency:1")
    await scenario.before_upstream()
