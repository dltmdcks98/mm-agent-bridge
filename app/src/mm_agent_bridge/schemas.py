from pydantic import BaseModel, Field, field_validator


class MattermostWebhookRequest(BaseModel):
    request_id: str = Field(min_length=1, max_length=64)
    user_id: str = Field(min_length=1, max_length=128)
    channel_id: str = Field(min_length=1, max_length=128)
    text: str = Field(min_length=1)
    token: str | None = Field(default=None, max_length=256)

    @field_validator("text")
    @classmethod
    def validate_text_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be blank")
        return value


class BridgeAcceptedResponse(BaseModel):
    request_id: str
    task_id: int
    status: str


class TaskStatusResponse(BaseModel):
    task_id: int
    status: str
    engine: str
    summary: str | None
