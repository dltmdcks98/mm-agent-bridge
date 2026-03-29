import secrets

from fastapi import HTTPException, status

from mm_agent_bridge.config import Settings


def validate_mattermost_token(
    *,
    settings: Settings,
    header_token: str | None,
    payload_token: str | None,
) -> None:
    expected = settings.mattermost_webhook_token
    if not expected:
        return

    provided = header_token or payload_token
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid mattermost token",
        )
