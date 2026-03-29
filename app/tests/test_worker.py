import pytest
from fastapi.testclient import TestClient
from mm_agent_bridge.config import get_settings
from mm_agent_bridge.db import Base, get_db
from mm_agent_bridge.main import app
from mm_agent_bridge.services import task_worker
from mm_agent_bridge.services.executor import ExecutorError
from mm_agent_bridge.services.task_worker import process_next_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(autouse=True)
def clear_runtime_settings(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("MM_BRIDGE_MATTERMOST_WEBHOOK_TOKEN", raising=False)
    monkeypatch.delenv("MM_BRIDGE_MATTERMOST_TOKEN_HEADER", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _make_test_client() -> tuple[TestClient, sessionmaker]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), testing_session_local


def test_process_next_task_marks_completed_and_updates_status_api() -> None:
    client, testing_session_local = _make_test_client()
    queue_resp = client.post(
        "/webhooks/mattermost",
        json={
            "request_id": "req-worker-1",
            "user_id": "u-1",
            "channel_id": "c-1",
            "text": "run this task",
        },
    )
    assert queue_resp.status_code == 202
    task_id = queue_resp.json()["task_id"]

    with testing_session_local() as db:
        processed = process_next_task(db)

    assert processed is not None
    assert processed.id == task_id
    assert processed.status == "completed"
    assert processed.summary == "[mock-executor] run this task"

    status_resp = client.get(f"/tasks/{task_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "completed"


def test_process_next_task_returns_none_when_empty_queue() -> None:
    _, testing_session_local = _make_test_client()
    with testing_session_local() as db:
        assert process_next_task(db) is None


def test_process_next_task_posts_callback_when_response_url_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, str] = {}

    def fake_post_worker_result(response_url: str, summary: str) -> None:
        captured["response_url"] = response_url
        captured["summary"] = summary

    monkeypatch.setattr(task_worker, "post_worker_result", fake_post_worker_result)
    client, testing_session_local = _make_test_client()
    queue_resp = client.post(
        "/webhooks/mattermost",
        json={
            "request_id": "req-worker-callback",
            "user_id": "u-1",
            "channel_id": "c-1",
            "response_url": "https://mattermost.example/hooks/abc",
            "text": "send callback",
        },
    )
    assert queue_resp.status_code == 202

    with testing_session_local() as db:
        processed = process_next_task(db)

    assert processed is not None
    assert processed.status == "completed"
    assert captured["response_url"] == "https://mattermost.example/hooks/abc"
    assert captured["summary"] == "[mock-executor] send callback"


def test_process_next_task_marks_failed_when_executor_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_execute_task(*, text: str, settings) -> str:
        raise ExecutorError("codex cli failed: bad auth")

    monkeypatch.setattr(task_worker, "execute_task", fake_execute_task)
    client, testing_session_local = _make_test_client()
    queue_resp = client.post(
        "/webhooks/mattermost",
        json={
            "request_id": "req-worker-fail",
            "user_id": "u-1",
            "channel_id": "c-1",
            "text": "will fail",
        },
    )
    assert queue_resp.status_code == 202

    with testing_session_local() as db:
        processed = process_next_task(db)

    assert processed is not None
    assert processed.status == "failed"
    assert processed.summary == "codex cli failed: bad auth"
