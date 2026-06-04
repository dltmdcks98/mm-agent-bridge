import pytest
from mm_agent_bridge.config import Settings
from mm_agent_bridge.services import agent_runtime
from mm_agent_bridge.services.agent_runtime import (
    AgentRequest,
    AgentResult,
    ExecutorAgentRuntime,
    build_agent_runtime,
)
from mm_agent_bridge.services.executor import ExecutorError


def test_executor_agent_runtime_delegates_to_execute_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(executor_backend="mock")
    request = AgentRequest(
        message_id=1,
        request_id="req-1",
        user_id="u-1",
        channel_id="c-1",
        text="hello",
    )

    def fake_execute_task(*, text: str, settings: Settings) -> str:
        assert text == "hello"
        assert settings.executor_backend == "mock"
        return "runtime-summary"

    monkeypatch.setattr(agent_runtime, "execute_task", fake_execute_task)
    runtime = ExecutorAgentRuntime(settings=settings)

    result = runtime.run(request)

    assert result == AgentResult(summary="runtime-summary")


def test_executor_agent_runtime_propagates_executor_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(executor_backend="mock")
    request = AgentRequest(
        message_id=2,
        request_id="req-2",
        user_id="u-2",
        channel_id="c-2",
        text="hello",
    )

    def fake_execute_task(*, text: str, settings: Settings) -> str:
        raise ExecutorError("boom")

    monkeypatch.setattr(agent_runtime, "execute_task", fake_execute_task)
    runtime = ExecutorAgentRuntime(settings=settings)

    with pytest.raises(ExecutorError, match="boom"):
        runtime.run(request)


def test_build_agent_runtime_returns_executor_runtime() -> None:
    runtime = build_agent_runtime(settings=Settings(executor_backend="mock"))
    assert isinstance(runtime, ExecutorAgentRuntime)
