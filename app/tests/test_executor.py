import subprocess

import pytest
from mm_agent_bridge.config import Settings
from mm_agent_bridge.services.executor import ExecutorError, execute_task


def test_execute_task_mock_backend_returns_expected_summary() -> None:
    settings = Settings(executor_backend="mock")
    summary = execute_task(text="hello", settings=settings)
    assert summary == "[mock-executor] hello"


def test_execute_task_codex_backend_builds_and_reads_stdout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        executor_backend="codex_cli",
        codex_cli_command="codex",
        codex_cli_args="--dangerously-skip-permissions",
    )

    def fake_run(command, check, capture_output, text, timeout):
        assert command == ["codex", "exec", "prompt", "--dangerously-skip-permissions"]
        assert check is False
        assert capture_output is True
        assert text is True
        assert timeout == settings.executor_timeout_seconds
        return subprocess.CompletedProcess(command, 0, stdout="done", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    summary = execute_task(text="prompt", settings=settings)
    assert summary == "done"


def test_execute_task_codex_backend_raises_on_nonzero_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(executor_backend="codex_cli")

    def fake_run(command, check, capture_output, text, timeout):
        return subprocess.CompletedProcess(command, 2, stdout="", stderr="boom")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(ExecutorError, match="codex cli failed"):
        execute_task(text="prompt", settings=settings)


def test_execute_task_claude_backend_builds_and_reads_stdout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        executor_backend="claude_cli",
        claude_cli_command="claude",
        claude_cli_args="--verbose",
    )

    def fake_run(command, check, capture_output, text, timeout):
        assert command == ["claude", "--print", "prompt", "--verbose"]
        assert check is False
        assert capture_output is True
        assert text is True
        assert timeout == settings.executor_timeout_seconds
        return subprocess.CompletedProcess(command, 0, stdout="claude-done", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    summary = execute_task(text="prompt", settings=settings)
    assert summary == "claude-done"


def test_execute_task_claude_backend_raises_on_nonzero_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(executor_backend="claude_cli")

    def fake_run(command, check, capture_output, text, timeout):
        return subprocess.CompletedProcess(command, 2, stdout="", stderr="bad request")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(ExecutorError, match="claude cli failed"):
        execute_task(text="prompt", settings=settings)
