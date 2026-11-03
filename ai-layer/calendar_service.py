from googleapiclient.discovery import build
from google_auth import get_google_credentials


def get_calendar_service():
    credentials = get_google_credentials()

    service = build(
        "calendar",
        "v3",
        credentials=credentials
    )

    return service


def get_free_busy(
    calendar_ids,
    time_min,
    time_max,
    timezone="Asia/Kolkata"
):
    service = get_calendar_service()

    body = {
        "timeMin": time_min,
        "timeMax": time_max,
        "timeZone": timezone,
        "items": [
            {"id": calendar_id}
            for calendar_id in calendar_ids
        ]
    }

    response = service.freebusy().query(
        body=body
    ).execute()

    return response

def get_calendar_busy_periods(
    calendar_id,
    time_min,
    time_max,
    timezone="Asia/Kolkata"
):
    service = get_calendar_service()

    body = {
        "timeMin": time_min,
        "timeMax": time_max,
        "timeZone": timezone,
        "items": [
            {"id": calendar_id}
        ]
    }

    response = service.freebusy().query(
        body=body
    ).execute()

    return response["calendars"][calendar_id]["busy"]

def create_calendar_event(
    title,
    start_time,
    end_time,
    guest_email,
    timezone="Asia/Kolkata"
):
    service = get_calendar_service()

    event = {
        "summary": title,
        "start": {
            "dateTime": start_time,
            "timeZone": timezone
        },
        "end": {
            "dateTime": end_time,
            "timeZone": timezone
        },
        "attendees": [
            {
                "email": guest_email
            }
        ]
    }

    created_event = service.events().insert(
        calendarId="primary",
        body=event,
        sendUpdates="all"
    ).execute()

    return created_event