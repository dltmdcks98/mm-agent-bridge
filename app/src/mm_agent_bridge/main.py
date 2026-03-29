from fastapi import Depends, FastAPI, HTTPException, Request, status
from sqlalchemy.orm import Session

from mm_agent_bridge.config import get_settings
from mm_agent_bridge.db import check_db_connection, get_db
from mm_agent_bridge.models import AgentTask
from mm_agent_bridge.schemas import (
    BridgeAcceptedResponse,
    MattermostWebhookRequest,
    TaskStatusResponse,
)
from mm_agent_bridge.security import validate_mattermost_token
from mm_agent_bridge.services.bridge_service import (
    DuplicateRequestError,
    enqueue_mattermost_request,
)

settings = get_settings()
app = FastAPI(title=settings.app_name)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        check_db_connection(db)
    except Exception as exc:  # pragma: no cover - defensive path
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database not ready",
        ) from exc
    return {"status": "ready"}


@app.post(
    "/webhooks/mattermost",
    response_model=BridgeAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def receive_mattermost_webhook(
    request: Request,
    payload: MattermostWebhookRequest,
    db: Session = Depends(get_db),
) -> BridgeAcceptedResponse:
    runtime_settings = get_settings()
    header_token = request.headers.get(runtime_settings.mattermost_token_header)
    validate_mattermost_token(
        settings=runtime_settings,
        header_token=header_token,
        payload_token=payload.token,
    )

    try:
        task = enqueue_mattermost_request(db, payload)
    except DuplicateRequestError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return BridgeAcceptedResponse(
        request_id=payload.request_id,
        task_id=task.id,
        status=task.status,
    )


@app.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: int, db: Session = Depends(get_db)) -> TaskStatusResponse:
    task = db.get(AgentTask, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    return TaskStatusResponse(
        task_id=task.id,
        status=task.status,
        engine=task.engine,
        summary=task.summary,
    )
