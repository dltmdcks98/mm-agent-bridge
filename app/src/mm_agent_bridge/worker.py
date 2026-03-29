import argparse
import time

from mm_agent_bridge.db import SessionLocal
from mm_agent_bridge.services.task_worker import process_next_task


def run_worker(*, once: bool, poll_interval: float) -> None:
    while True:
        with SessionLocal() as db:
            task = process_next_task(db)
            if task is not None:
                print(f"processed task_id={task.id} status={task.status}")

        if once:
            break
        time.sleep(poll_interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run task worker for mm-agent-bridge")
    parser.add_argument("--once", action="store_true", help="Process at most one queued task")
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=1.0,
        help="Polling interval in seconds when running continuously",
    )
    args = parser.parse_args()
    run_worker(once=args.once, poll_interval=args.poll_interval)


if __name__ == "__main__":
    main()
