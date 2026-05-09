from pydantic import BaseModel


class ReminderMessage(BaseModel):
    reminder_id: str
    user_id: str
    event_id: str
    event_title: str
    event_start: str | None = None
    remind_at: str
    channels: list[str]
    message: str | None = None
    user_email: str | None = None
