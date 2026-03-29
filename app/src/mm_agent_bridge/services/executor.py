import subprocess

from mm_agent_bridge.config import Settings


class ExecutorError(RuntimeError):
    pass


def execute_task(*, text: str, settings: Settings) -> str:
    backend = settings.executor_backend
    if backend == "mock":
        return f"[mock-executor] {text.strip()}"
    if backend == "codex_cli":
        return execute_with_codex_cli(text=text, settings=settings)
    if backend == "claude_cli":
        return execute_with_claude_cli(text=text, settings=settings)
    raise ExecutorError(f"unsupported executor backend: {backend}")


def execute_with_codex_cli(*, text: str, settings: Settings) -> str:
    command = [settings.codex_cli_command, "exec", text]
    if settings.codex_cli_args:
        command.extend(settings.codex_cli_args.split())

    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=settings.executor_timeout_seconds,
        )
    except FileNotFoundError as exc:
        raise ExecutorError("codex cli command not found") from exc
    except subprocess.TimeoutExpired as exc:
        raise ExecutorError("codex cli execution timed out") from exc

    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip() or "no stderr"
        raise ExecutorError(f"codex cli failed: {stderr}")

    stdout = (completed.stdout or "").strip()
    if not stdout:
        raise ExecutorError("codex cli returned empty output")
    return stdout


def execute_with_claude_cli(*, text: str, settings: Settings) -> str:
    command = [settings.claude_cli_command, "--print", text]
    if settings.claude_cli_args:
        command.extend(settings.claude_cli_args.split())

    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=settings.executor_timeout_seconds,
        )
    except FileNotFoundError as exc:
        raise ExecutorError("claude cli command not found") from exc
    except subprocess.TimeoutExpired as exc:
        raise ExecutorError("claude cli execution timed out") from exc

    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip() or "no stderr"
        raise ExecutorError(f"claude cli failed: {stderr}")

    stdout = (completed.stdout or "").strip()
    if not stdout:
        raise ExecutorError("claude cli returned empty output")
    return stdout
