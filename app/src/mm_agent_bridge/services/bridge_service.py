from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mm_agent_bridge.models import AgentTask, IncomingMessage
from mm_agent_bridge.schemas import MattermostWebhookRequest


class DuplicateRequestError(ValueError):
    pass


def enqueue_mattermost_request(db: Session, payload: MattermostWebhookRequest) -> AgentTask:
    try:
        message = IncomingMessage(
            request_id=payload.request_id,
            user_id=payload.user_id,
            channel_id=payload.channel_id,
            response_url=payload.response_url,
            text=payload.text,
        )
        db.add(message)
        db.flush()

        task = AgentTask(message_id=message.id, status="queued", engine="codex")
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateRequestError(
            f"request_id already exists: {payload.request_id}",
        ) from exc
