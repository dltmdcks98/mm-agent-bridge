import pytest
from fastapi.testclient import TestClient
from mm_agent_bridge.config import get_settings
from mm_agent_bridge.db import Base, get_db
from mm_agent_bridge.main import app
from mm_agent_bridge.models import AgentTask, IncomingMessage
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


def test_mattermost_webhook_is_queued() -> None:
    client, _ = _make_test_client()

    response = client.post(
        "/webhooks/mattermost",
        json={
            "request_id": "req-1",
            "user_id": "u-1",
            "channel_id": "c-1",
            "text": "hello bridge",
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert body["request_id"] == "req-1"
    assert body["status"] == "queued"
    assert isinstance(body["task_id"], int)


def test_readyz_returns_ready() -> None:
    client, _ = _make_test_client()
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_duplicate_request_id_returns_409() -> None:
    client, _ = _make_test_client()
    payload = {
        "request_id": "same-id",
        "user_id": "u-1",
        "channel_id": "c-1",
        "text": "hello",
    }

    first = client.post("/webhooks/mattermost", json=payload)
    second = client.post("/webhooks/mattermost", json=payload)

    assert first.status_code == 202
    assert second.status_code == 409


def test_duplicate_request_does_not_create_extra_rows() -> None:
    client, testing_session_local = _make_test_client()
    payload = {
        "request_id": "same-id",
        "user_id": "u-1",
        "channel_id": "c-1",
        "text": "hello",
    }

    client.post("/webhooks/mattermost", json=payload)
    client.post("/webhooks/mattermost", json=payload)

    with testing_session_local() as db:
        assert db.query(IncomingMessage).count() == 1
        assert db.query(AgentTask).count() == 1


def test_blank_text_returns_422() -> None:
    client, _ = _make_test_client()
    response = client.post(
        "/webhooks/mattermost",
        json={
            "request_id": "req-blank",
            "user_id": "u-1",
            "channel_id": "c-1",
            "text": "   ",
        },
    )
    assert response.status_code == 422


def test_webhook_requires_token_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MM_BRIDGE_MATTERMOST_WEBHOOK_TOKEN", "secret-token")
    get_settings.cache_clear()
    client, _ = _make_test_client()
    response = client.post(
        "/webhooks/mattermost",
        json={
            "request_id": "req-auth-1",
            "user_id": "u-1",
            "channel_id": "c-1",
            "text": "hello",
        },
    )
    assert response.status_code == 401


def test_webhook_accepts_valid_header_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MM_BRIDGE_MATTERMOST_WEBHOOK_TOKEN", "secret-token")
    monkeypatch.setenv("MM_BRIDGE_MATTERMOST_TOKEN_HEADER", "X-Test-Token")
    get_settings.cache_clear()
    client, _ = _make_test_client()
    response = client.post(
        "/webhooks/mattermost",
        headers={"X-Test-Token": "secret-token"},
        json={
            "request_id": "req-auth-2",
            "user_id": "u-1",
            "channel_id": "c-1",
            "text": "hello",
        },
    )
    assert response.status_code == 202
