from typing import TypedDict, Optional, List


class MeetingState(TypedDict, total=False):

    email_content: str

    meeting_required: bool

    meeting_title: str

    guest_email: str

    duration_minutes: int

    preferred_dates: List[str]

    preferred_times: List[str]

    invalid_time: bool

    invalid_duration: bool

    host_availability: List[dict]

    guest_availability: List[dict]

    common_slots: List[dict]

    selected_slot: Optional[dict]

    event_id: Optional[str]

    event_link: Optional[str]

    status: str

    error: Optional[str]