from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ChannelEnum(str, Enum):
    email = "email"


class ReminderCreate(BaseModel):
    event_id: str
    remind_at: datetime
    channels: list[ChannelEnum] = [ChannelEnum.email]
    message: str | None = None

    @model_validator(mode="after")
    def remind_at_must_be_future(self):
        from datetime import timezone
        if self.remind_at <= datetime.now(timezone.utc):
            raise ValueError("remind_at must be in the future")
        return self


class ReminderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_id: str
    user_id: str
    remind_at: datetime
    channels: list[str]
    status: str
    message: str | None
    created_at: datetime


class ReminderUpdate(BaseModel):
    remind_at: datetime | None = None
    channels: list[ChannelEnum] | None = None
    message: str | None = None
