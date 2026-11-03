from calendar_service import get_free_busy


if __name__ == "__main__":

    result = get_free_busy(
        calendar_ids=[
            "primary",
            "sanjaykrishna9454@gmail.com"
        ],
        time_min="2026-09-28T09:00:00+05:30",
        time_max="2026-09-28T18:00:00+05:30",
        timezone="Asia/Kolkata"
    )

    print("\nCalendar availability:\n")

    for calendar_id, data in result["calendars"].items():

        print("--------------------------------")
        print("Calendar:", calendar_id)
        print("Busy periods:")

        for busy in data["busy"]:
            print(
                busy["start"],
                "→",
                busy["end"]
            )