from pydantic import BaseModel, Field
from typing import List


class SchedulingIntent(BaseModel):

    meeting_required: bool

    meeting_title: str = Field(
        default="General Meeting"
    )

    guest_email: str | None = None

    duration_minutes: int = 30

    preferred_dates: List[str] = Field(
        default_factory=list
    )

    preferred_times: List[str] = Field(
        default_factory=list
    )

    invalid_time: bool = False

    invalid_duration: bool = False

    reason: str = ""