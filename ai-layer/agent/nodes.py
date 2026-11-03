from datetime import datetime, timedelta

from config import settings

from langchain_core.messages import (
    SystemMessage,
    HumanMessage
)

from llm.prompts import SYSTEM_PROMPT

from agent.state import MeetingState
from llm.client import llm
from schemas.scheduling import SchedulingIntent

from calendar_service import (
    get_free_busy,
    create_calendar_event
)

from availability import (
    calculate_available_slots,
    find_common_slots
)


# ============================================================
# DATE PARSING HELPER
# ============================================================

def parse_preferred_date(date_text: str):

    if not date_text:
        return None

    date_text = date_text.strip().lower()

    today = datetime.now().date()

    # --------------------------------------------------------
    # Relative dates
    # --------------------------------------------------------

    if date_text == "today":
        return today

    if date_text == "tomorrow":
        return today + timedelta(days=1)

    if date_text == "day after tomorrow":
        return today + timedelta(days=2)

    # --------------------------------------------------------
    # Weekday handling
    # --------------------------------------------------------

    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }

    # "this Monday", "this Friday", etc.
    if date_text.startswith("this "):

        weekday_name = date_text.replace(
            "this ",
            "",
            1
        ).strip()

        if weekday_name in weekdays:

            target_weekday = weekdays[
                weekday_name
            ]

            days_ahead = (
                target_weekday
                - today.weekday()
            ) % 7

            return today + timedelta(
                days=days_ahead
            )

    # "next Monday", "next Friday", etc.
    if date_text.startswith("next "):

        weekday_name = date_text.replace(
            "next ",
            "",
            1
        ).strip()

        if weekday_name in weekdays:

            target_weekday = weekdays[
                weekday_name
            ]

            days_ahead = (
                target_weekday
                - today.weekday()
            ) % 7

            if days_ahead == 0:
                days_ahead = 7
            else:
                days_ahead += 7

            return today + timedelta(
                days=days_ahead
            )

    # --------------------------------------------------------
    # YYYY-MM-DD
    # --------------------------------------------------------

    try:

        return datetime.strptime(
            date_text,
            "%Y-%m-%d"
        ).date()

    except ValueError:
        pass

    # --------------------------------------------------------
    # October 5, 2026
    # --------------------------------------------------------

    try:

        return datetime.strptime(
            date_text.title(),
            "%B %d, %Y"
        ).date()

    except ValueError:
        pass

    # --------------------------------------------------------
    # Oct 5, 2026
    # --------------------------------------------------------

    try:

        return datetime.strptime(
            date_text.title(),
            "%b %d, %Y"
        ).date()

    except ValueError:
        pass

    return None


# ============================================================
# 1. ANALYZE EMAIL
# ============================================================

def analyze_email(
    state: MeetingState
) -> MeetingState:

    print("Analyzing email with Claude...")

    email_content = state.get(
        "email_content",
        ""
    )

    try:

        # ----------------------------------------------------
        # Create structured Claude model
        # ----------------------------------------------------

        structured_llm = llm.with_structured_output(
            SchedulingIntent
        )

        # ----------------------------------------------------
        # Send system instructions separately
        # from the untrusted email content
        # ----------------------------------------------------

        result = structured_llm.invoke(
            [
                SystemMessage(
                    content=SYSTEM_PROMPT
                ),
                HumanMessage(
                    content=email_content
                )
            ]
        )

        # ----------------------------------------------------
        # Store extracted information
        # ----------------------------------------------------

        state["meeting_required"] = (
            result.meeting_required
        )

        state["meeting_title"] = (
            result.meeting_title
        )

        # If Claude does not provide guest email,
        # use the configured guest email from .env
        state["guest_email"] = (
            result.guest_email
            or settings.guest_email
        )

        state["duration_minutes"] = (
            result.duration_minutes
        )

        # ----------------------------------------------------
        # Handle preferred dates
        # ----------------------------------------------------

        preferred_dates = (
            result.preferred_dates.copy()
        )

        # Claude may understand "tomorrow" from the email
        # but may not always place it inside preferred_dates.
        #
        # Therefore, if no date was extracted, check the
        # email content and Claude's reason for relative dates.

        if not preferred_dates:

            text_to_check = (
                email_content
                + " "
                + result.reason
            ).lower()

            if "day after tomorrow" in text_to_check:

                preferred_dates.append(
                    "day after tomorrow"
                )

            elif "tomorrow" in text_to_check:

                preferred_dates.append(
                    "tomorrow"
                )

            elif "today" in text_to_check:

                preferred_dates.append(
                    "today"
                )

        state["preferred_dates"] = (
            preferred_dates
        )

        state["preferred_times"] = (
            result.preferred_times
        )

        # ----------------------------------------------------
        # Store validation flags
        # ----------------------------------------------------

        state["invalid_time"] = (
            result.invalid_time
        )

        state["invalid_duration"] = (
            result.invalid_duration
        )

        state["status"] = (
            "Email analyzed successfully"
        )

        # ----------------------------------------------------
        # Print extracted information
        # ----------------------------------------------------

        print(
            "Meeting required:",
            result.meeting_required
        )

        print(
            "Meeting title:",
            result.meeting_title
        )

        print(
            "Guest email:",
            state["guest_email"]
        )

        print(
            "Duration:",
            result.duration_minutes
        )

        print(
            "Preferred dates:",
            state["preferred_dates"]
        )

        print(
            "Preferred times:",
            state["preferred_times"]
        )

        print(
            "Invalid time:",
            result.invalid_time
        )

        print(
            "Invalid duration:",
            result.invalid_duration
        )

        print(
            "Reason:",
            result.reason
        )

    except Exception as e:

        state["status"] = (
            "Email analysis failed"
        )

        state["error"] = str(e)

        print(
            "Email analysis failed:",
            e
        )

    return state


# ============================================================
# 2. CHECK WHETHER MEETING IS REQUIRED
# ============================================================

def check_meeting_required(
    state: MeetingState
) -> str:

    # Invalid time must continue to the scheduling branch
    # so check_calendars() can stop the workflow cleanly.

    if state.get(
        "invalid_time",
        False
    ):
        return "schedule"

    # Invalid duration must also continue to the scheduling
    # branch so check_calendars() can stop the workflow.

    if state.get(
        "invalid_duration",
        False
    ):
        return "schedule"

    # Normal meeting request

    if state.get(
        "meeting_required",
        False
    ):
        return "schedule"

    # Normal email with no meeting request

    return "end"


# ============================================================
# 3. CHECK GOOGLE CALENDARS
# ============================================================

def check_calendars(
    state: MeetingState
) -> MeetingState:

    print(
        "Checking Google Calendars..."
    )

    # --------------------------------------------------------
    # INVALID TIME
    # --------------------------------------------------------

    if state.get(
        "invalid_time",
        False
    ):

        state["status"] = (
            "Invalid meeting time"
        )

        state["error"] = (
            "The email contains an invalid meeting time. "
            "Please provide a valid time."
        )

        print(
            "Invalid meeting time found."
        )

        print(
            "Stopping scheduling workflow."
        )

        return state

    # --------------------------------------------------------
    # INVALID DURATION
    # --------------------------------------------------------

    if state.get(
        "invalid_duration",
        False
    ):

        state["status"] = (
            "Invalid meeting duration"
        )

        state["error"] = (
            "The email contains an invalid meeting duration. "
            "Meeting duration must be between 15 and 240 minutes."
        )

        print(
            "Invalid meeting duration found."
        )

        print(
            "Stopping scheduling workflow."
        )

        return state

    # --------------------------------------------------------
    # 1. CHECK PREFERRED DATE
    # --------------------------------------------------------

    preferred_dates = state.get(
        "preferred_dates",
        []
    )

    if not preferred_dates:

        state["status"] = (
            "No preferred date found"
        )

        state["error"] = (
            "The email did not contain a meeting date."
        )

        print(
            "No preferred date found."
        )

        return state

    # --------------------------------------------------------
    # 2. CHECK GUEST EMAIL
    # --------------------------------------------------------

    guest_email = state.get(
        "guest_email"
    )

    if not guest_email:

        state["status"] = (
            "Guest email missing"
        )

        state["error"] = (
            "Guest email was not available."
        )

        print(
            "Guest email is missing."
        )

        return state

    duration = state.get(
        "duration_minutes",
        30
    )

    all_common_slots = []

    all_host_slots = []

    all_guest_slots = []

    # --------------------------------------------------------
    # 3. PROCESS EVERY PREFERRED DATE
    # --------------------------------------------------------

    for preferred_date in preferred_dates:

        print(
            "----------------------------------------------"
        )

        print(
            "Processing date:",
            preferred_date
        )

        requested_date = parse_preferred_date(
            preferred_date
        )

        if requested_date is None:

            print(
                "Could not understand date:",
                preferred_date
            )

            continue

        # ----------------------------------------------------
        # Calendar working hours
        # ----------------------------------------------------

        time_min = (
            f"{requested_date}T09:00:00+05:30"
        )

        time_max = (
            f"{requested_date}T18:00:00+05:30"
        )

        print(
            "Calendar search date:",
            requested_date
        )

        print(
            "Search start:",
            time_min
        )

        print(
            "Search end:",
            time_max
        )

        try:

            # ------------------------------------------------
            # Get real Google Calendar busy periods
            # ------------------------------------------------

            calendar_result = get_free_busy(
                calendar_ids=[
                    "primary",
                    guest_email
                ],
                time_min=time_min,
                time_max=time_max,
                timezone="Asia/Kolkata"
            )

            host_busy = calendar_result[
                "calendars"
            ][
                "primary"
            ][
                "busy"
            ]

            guest_busy = calendar_result[
                "calendars"
            ][
                guest_email
            ][
                "busy"
            ]

            print(
                "Host busy periods:",
                host_busy
            )

            print(
                "Guest busy periods:",
                guest_busy
            )

            # ------------------------------------------------
            # Calculate host available slots
            # ------------------------------------------------

            host_slots = calculate_available_slots(
                busy_periods=host_busy,
                start_time=time_min,
                end_time=time_max,
                duration_minutes=duration
            )

            # ------------------------------------------------
            # Calculate guest available slots
            # ------------------------------------------------

            guest_slots = calculate_available_slots(
                busy_periods=guest_busy,
                start_time=time_min,
                end_time=time_max,
                duration_minutes=duration
            )

            # ------------------------------------------------
            # Find common availability
            # ------------------------------------------------

            common_slots = find_common_slots(
                host_busy=host_busy,
                guest_busy=guest_busy,
                start_time=time_min,
                end_time=time_max,
                duration_minutes=duration
            )

            # ------------------------------------------------
            # Store results
            # ------------------------------------------------

            all_host_slots.extend(
                host_slots
            )

            all_guest_slots.extend(
                guest_slots
            )

            all_common_slots.extend(
                common_slots
            )

            print(
                "Host available slots:",
                host_slots
            )

            print(
                "Guest available slots:",
                guest_slots
            )

            print(
                "Common available slots:",
                common_slots
            )

        except Exception as e:

            print(
                f"Calendar check failed for "
                f"{preferred_date}:",
                e
            )

    # --------------------------------------------------------
    # 4. CHECK WHETHER CALENDAR DATA WAS RETRIEVED
    # --------------------------------------------------------

    if (
        not all_host_slots
        or not all_guest_slots
    ):

        state["status"] = (
            "No calendar availability found"
        )

        state["error"] = (
            "No availability could be retrieved "
            "for the requested dates."
        )

        print(
            "No calendar availability found."
        )

        return state

    # --------------------------------------------------------
    # 5. CHECK COMMON AVAILABILITY
    # --------------------------------------------------------

    if not all_common_slots:

        state["status"] = (
            "No common availability"
        )

        state["error"] = (
            "No common available slots found."
        )

        state["host_availability"] = (
            all_host_slots
        )

        state["guest_availability"] = (
            all_guest_slots
        )

        state["common_slots"] = []

        print(
            "No common available slots found."
        )

        return state

    # --------------------------------------------------------
    # 6. STORE AVAILABILITY IN STATE
    # --------------------------------------------------------

    state["host_availability"] = (
        all_host_slots
    )

    state["guest_availability"] = (
        all_guest_slots
    )

    state["common_slots"] = (
        all_common_slots
    )

    state["status"] = (
        "Real calendar availability retrieved"
    )

    state["error"] = None

    # --------------------------------------------------------
    # 7. PRINT FINAL COMMON AVAILABILITY
    # --------------------------------------------------------

    print(
        "=============================================="
    )

    print(
        "COMMON AVAILABLE SLOTS"
    )

    print(
        "=============================================="
    )

    print(
        all_common_slots
    )

    print(
        "=============================================="
    )

    return state


# ============================================================
# 4. FIND COMMON AVAILABLE TIME
# ============================================================

def find_common_time(
    state: MeetingState
):

    common_slots = state.get(
        "common_slots",
        []
    )

    preferred_dates = state.get(
        "preferred_dates",
        []
    )

    preferred_times = state.get(
        "preferred_times",
        []
    )

    if not common_slots:

        state["error"] = (
            "No common available slots found."
        )

        state["selected_slot"] = None

        return state

    print(
        "=============================================="
    )

    print(
        "SLOT SELECTION"
    )

    print(
        "=============================================="
    )

    print(
        "Preferred dates:",
        preferred_dates
    )

    print(
        "Preferred times:",
        preferred_times
    )

    print(
        "Common slots:",
        common_slots
    )

    # --------------------------------------------------
    # STEP 1: FILTER BY PREFERRED DATE
    # --------------------------------------------------

    date_filtered_slots = common_slots

    if preferred_dates:

        requested_dates = set()

        for date_text in preferred_dates:

            parsed_date = parse_preferred_date(
                date_text
            )

            if parsed_date:

                requested_dates.add(
                    parsed_date.isoformat()
                )

        if requested_dates:

            date_filtered_slots = [
                slot
                for slot in common_slots
                if slot["start"][:10]
                in requested_dates
            ]

    if (
        preferred_dates
        and not date_filtered_slots
    ):

        state["error"] = (
            "No common availability found "
            "on the requested date."
        )

        state["selected_slot"] = None

        return state

    # --------------------------------------------------
    # STEP 2: NO TIME PREFERENCE
    # --------------------------------------------------

    if not preferred_times:

        date_filtered_slots.sort(
            key=lambda slot: slot["start"]
        )

        selected_slot = (
            date_filtered_slots[0]
        )

        state["common_slots"] = (
            date_filtered_slots
        )

        state["selected_slot"] = (
            selected_slot
        )

        print(
            "No specific time requested."
        )

        print(
            "Selected earliest slot:",
            selected_slot
        )

        return state

    # --------------------------------------------------
    # STEP 3: CONVERT PREFERRED TIME
    # --------------------------------------------------

    def parse_time(
        time_text
    ):

        time_text = (
            time_text
            .strip()
            .lower()
            .replace(".", "")
        )

        time_text = time_text.replace(
            "at ",
            ""
        ).strip()

        formats = [
            "%I %p",
            "%I:%M %p",
            "%H:%M",
            "%H:%M:%S"
        ]

        for fmt in formats:

            try:

                return datetime.strptime(
                    time_text,
                    fmt
                ).time()

            except ValueError:
                pass

        return None

    # --------------------------------------------------
    # STEP 4: FIND EXACT REQUESTED SLOT
    # --------------------------------------------------

    exact_matches = []

    for slot in date_filtered_slots:

        slot_start = datetime.fromisoformat(
            slot["start"]
        )

        hour = slot_start.hour
        minute = slot_start.minute

        for preferred_time in preferred_times:

            preferred_time = (
                preferred_time
                .strip()
                .lower()
            )

            # Morning
            if preferred_time == "morning":

                if 9 <= hour < 12:

                    exact_matches.append(
                        slot
                    )

            # Afternoon
            elif preferred_time == "afternoon":

                if 12 <= hour < 17:

                    exact_matches.append(
                        slot
                    )

            # Evening
            elif preferred_time == "evening":

                if 17 <= hour < 20:

                    exact_matches.append(
                        slot
                    )

            # Exact time
            else:

                requested_time = parse_time(
                    preferred_time
                )

                if requested_time:

                    if (
                        hour
                        == requested_time.hour
                        and minute
                        == requested_time.minute
                    ):

                        exact_matches.append(
                            slot
                        )

    # --------------------------------------------------
    # REMOVE DUPLICATE SLOTS
    # --------------------------------------------------

    unique_exact_matches = []

    seen = set()

    for slot in exact_matches:

        key = (
            slot["start"],
            slot["end"]
        )

        if key not in seen:

            seen.add(
                key
            )

            unique_exact_matches.append(
                slot
            )

    # --------------------------------------------------
    # STEP 5: EXACT SLOT AVAILABLE
    # --------------------------------------------------

    if unique_exact_matches:

        unique_exact_matches.sort(
            key=lambda slot: slot["start"]
        )

        selected_slot = (
            unique_exact_matches[0]
        )

        state["common_slots"] = (
            unique_exact_matches
        )

        state["selected_slot"] = (
            selected_slot
        )

        print(
            "Exact requested time available."
        )

        print(
            "Selected slot:",
            selected_slot
        )

        return state

    # --------------------------------------------------
    # STEP 6: REQUESTED EXACT TIME UNAVAILABLE
    # Find nearest available slot
    # --------------------------------------------------

    requested_exact_times = []

    for preferred_time in preferred_times:

        preferred_time = (
            preferred_time
            .strip()
            .lower()
        )

        requested_time = parse_time(
            preferred_time
        )

        if requested_time:

            requested_exact_times.append(
                requested_time
            )

    # --------------------------------------------------
    # STEP 7: MORNING / AFTERNOON / EVENING FALLBACK
    # --------------------------------------------------

    if not requested_exact_times:

        fallback_slots = []

        for slot in date_filtered_slots:

            slot_start = datetime.fromisoformat(
                slot["start"]
            )

            hour = slot_start.hour

            for preferred_time in preferred_times:

                preference = (
                    preferred_time
                    .strip()
                    .lower()
                )

                if preference == "morning":

                    if 9 <= hour < 12:

                        fallback_slots.append(
                            slot
                        )

                elif preference == "afternoon":

                    if 12 <= hour < 17:

                        fallback_slots.append(
                            slot
                        )

                elif preference == "evening":

                    if 17 <= hour < 20:

                        fallback_slots.append(
                            slot
                        )

        if fallback_slots:

            fallback_slots.sort(
                key=lambda slot: slot["start"]
            )

            selected_slot = (
                fallback_slots[0]
            )

            state["common_slots"] = (
                fallback_slots
            )

            state["selected_slot"] = (
                selected_slot
            )

            print(
                "Requested time period unavailable."
            )

            print(
                "Selected fallback slot:",
                selected_slot
            )

            return state

    # --------------------------------------------------
    # STEP 8: FIND NEAREST EXACT-TIME ALTERNATIVE
    # --------------------------------------------------

    nearest_slot = None

    smallest_difference = None

    for slot in date_filtered_slots:

        slot_start = datetime.fromisoformat(
            slot["start"]
        )

        for requested_time in requested_exact_times:

            requested_datetime = (
                slot_start.replace(
                    hour=requested_time.hour,
                    minute=requested_time.minute,
                    second=0,
                    microsecond=0
                )
            )

            difference = abs(
                (
                    slot_start
                    - requested_datetime
                ).total_seconds()
            )

            if (
                smallest_difference is None
                or difference < smallest_difference
                or (
                    difference == smallest_difference
                    and nearest_slot is not None
                    and slot_start
                    > datetime.fromisoformat(
                        nearest_slot["start"]
                    )
                )
            ):

                smallest_difference = (
                    difference
                )

                nearest_slot = slot

    # --------------------------------------------------
    # STEP 9: SELECT NEAREST SLOT
    # --------------------------------------------------

    if nearest_slot:

        state["selected_slot"] = (
            nearest_slot
        )

        state["common_slots"] = (
            date_filtered_slots
        )

        print(
            "Exact requested time unavailable."
        )

        print(
            "Selecting nearest available slot:",
            nearest_slot
        )

        return state

    # --------------------------------------------------
    # STEP 10: NOTHING AVAILABLE
    # --------------------------------------------------

    state["error"] = (
        "No suitable common available "
        "slot found."
    )

    state["selected_slot"] = None

    return state


# ============================================================
# 5. CREATE GOOGLE CALENDAR MEETING
# ============================================================

def create_meeting(
    state: MeetingState
) -> MeetingState:

    print(
        "Creating meeting..."
    )

    selected_slot = state.get(
        "selected_slot"
    )

    # --------------------------------------------------------
    # No slot
    # --------------------------------------------------------

    if not selected_slot:

        state["status"] = (
            "Cannot create meeting: no slot selected"
        )

        state["error"] = (
            "No common meeting slot is available."
        )

        print(
            "Meeting was not created because "
            "no slot was selected."
        )

        return state

    try:

        meeting_title = state.get(
            "meeting_title",
            "General Meeting"
        )

        guest_email = state.get(
            "guest_email"
        )

        # ----------------------------------------------------
        # Create Google Calendar event
        # ----------------------------------------------------

        event = create_calendar_event(
            title=meeting_title,
            start_time=selected_slot["start"],
            end_time=selected_slot["end"],
            guest_email=guest_email,
            timezone="Asia/Kolkata"
        )

        # ----------------------------------------------------
        # Save event information
        # ----------------------------------------------------

        state["event_id"] = (
            event.get("id")
        )

        state["event_link"] = (
            event.get("htmlLink")
        )

        state["status"] = (
            "Meeting created successfully"
        )

        state["error"] = None

        print(
            "Calendar event created!"
        )

        print(
            "Event ID:",
            event.get("id")
        )

        print(
            "Event link:",
            event.get("htmlLink")
        )

    except Exception as e:

        state["status"] = (
            "Failed to create meeting"
        )

        state["error"] = str(e)

        print(
            "Calendar event creation failed:",
            e
        )

    return state


# ============================================================
# 6. SEND CONFIRMATION
# ============================================================

def send_confirmation(
    state: MeetingState
) -> MeetingState:

    print(
        "Sending confirmation..."
    )

    # Google Calendar sends the invitation
    # because create_calendar_event()
    # uses sendUpdates="all".

    if state.get(
        "event_id"
    ):

        state["status"] = (
            "Meeting scheduled successfully"
        )

        print(
            "Meeting invitation sent through "
            "Google Calendar."
        )

    else:

        state["status"] = (
            "Meeting could not be scheduled"
        )

        print(
            "No event ID found. "
            "Confirmation not sent."
        )

    return state