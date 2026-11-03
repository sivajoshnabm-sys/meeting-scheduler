from calendar_service import get_calendar_service


if __name__ == "__main__":

    service = get_calendar_service()

    calendar = service.calendars().get(
        calendarId="primary"
    ).execute()

    print("Google Calendar authentication successful!")
    print("Calendar:", calendar.get("summary"))
    print("Timezone:", calendar.get("timeZone"))