from uuid import UUID

from pydantic import BaseModel, Field


class CareerChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=4000)


class CareerChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    resume_id: UUID | None = None
    history: list[CareerChatMessage] = Field(default_factory=list, max_length=12)


class CareerChatResponse(BaseModel):
    response: str
