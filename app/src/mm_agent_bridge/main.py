from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from mm_agent_bridge.config import get_settings
from mm_agent_bridge.db import check_db_connection, get_db
from mm_agent_bridge.schemas import BridgeAcceptedResponse, MattermostWebhookRequest
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
    payload: MattermostWebhookRequest,
    db: Session = Depends(get_db),
) -> BridgeAcceptedResponse:
    try:
        task = enqueue_mattermost_request(db, payload)
    except DuplicateRequestError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return BridgeAcceptedResponse(
        request_id=payload.request_id,
        task_id=task.id,
        status=task.status,
    )
