from dataclasses import dataclass
from typing import Protocol

from mm_agent_bridge.config import Settings
from mm_agent_bridge.services.executor import execute_task


@dataclass(frozen=True, slots=True)
class AgentRequest:
    message_id: int
    request_id: str
    user_id: str
    channel_id: str
    text: str


@dataclass(frozen=True, slots=True)
class AgentResult:
    summary: str


class AgentRuntime(Protocol):
    def run(self, request: AgentRequest) -> AgentResult:
        ...


class ConversationSessionResolver(Protocol):
    def resolve_session_id(self, request: AgentRequest) -> str | None:
        ...


class ResponsePublisher(Protocol):
    # NOTE: root_id/thread policy must be decided by Mattermost-specific publishers,
    # not by runtime adapters.
    def publish_result(self, request: AgentRequest, result: AgentResult) -> None:
        ...


class ExecutorAgentRuntime:
    def __init__(self, *, settings: Settings) -> None:
        self._settings = settings

    def run(self, request: AgentRequest) -> AgentResult:
        summary = execute_task(text=request.text, settings=self._settings)
        return AgentResult(summary=summary)


def build_agent_runtime(*, settings: Settings) -> AgentRuntime:
    return ExecutorAgentRuntime(settings=settings)
