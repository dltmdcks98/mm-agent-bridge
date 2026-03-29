from sqlalchemy.orm import Session

from mm_agent_bridge.models import AgentTask, IncomingMessage
from mm_agent_bridge.services.mattermost_client import post_worker_result


def process_next_task(db: Session) -> AgentTask | None:
    task = (
        db.query(AgentTask)
        .filter(AgentTask.status == "queued")
        .order_by(AgentTask.id.asc())
        .first()
    )
    if task is None:
        return None

    task.status = "running"
    db.commit()
    db.refresh(task)

    try:
        message = db.get(IncomingMessage, task.message_id)
        if message is None:
            task.status = "failed"
            task.summary = "source message not found"
        else:
            # Placeholder executor: replace with Codex/Claude adapter.
            task.status = "completed"
            task.summary = f"[mock-executor] {message.text.strip()}"
            if message.response_url:
                post_worker_result(message.response_url, task.summary)
        db.commit()
        db.refresh(task)
        return task
    except Exception as exc:  # pragma: no cover - defensive path
        db.rollback()
        task.status = "failed"
        task.summary = f"worker error: {exc}"
        db.commit()
        db.refresh(task)
        return task
