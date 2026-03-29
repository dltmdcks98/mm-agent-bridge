from sqlalchemy.orm import Session

from mm_agent_bridge.config import get_settings
from mm_agent_bridge.models import AgentTask, IncomingMessage
from mm_agent_bridge.services.executor import ExecutorError, execute_task
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
            settings = get_settings()
            try:
                summary = execute_task(text=message.text, settings=settings)
                task.status = "completed"
                task.summary = summary
                if message.response_url:
                    post_worker_result(message.response_url, task.summary)
            except ExecutorError as exc:
                task.status = "failed"
                task.summary = str(exc)
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
