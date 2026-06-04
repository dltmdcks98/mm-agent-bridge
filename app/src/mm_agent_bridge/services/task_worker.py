from sqlalchemy.orm import Session

from mm_agent_bridge.config import get_settings
from mm_agent_bridge.models import AgentTask, IncomingMessage
from mm_agent_bridge.services.agent_runtime import AgentRequest, build_agent_runtime
from mm_agent_bridge.services.executor import ExecutorError
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
            runtime = build_agent_runtime(settings=settings)
            request = AgentRequest(
                message_id=message.id,
                request_id=message.request_id,
                user_id=message.user_id,
                channel_id=message.channel_id,
                text=message.text,
            )
            try:
                result = runtime.run(request)
                task.status = "completed"
                task.summary = result.summary
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
