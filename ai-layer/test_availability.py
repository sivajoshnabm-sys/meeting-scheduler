from availability import calculate_available_slots


if __name__ == "__main__":

    busy_periods = [
        {
            "start": "2026-09-28T11:00:00+05:30",
            "end": "2026-09-28T12:00:00+05:30"
        }
    ]

    available_slots = calculate_available_slots(
        busy_periods=busy_periods,
        start_time="2026-09-28T09:00:00+05:30",
        end_time="2026-09-28T18:00:00+05:30",
        duration_minutes=30
    )

    print("\nAvailable slots:\n")

    for slot in available_slots:
        print(
            slot["start"],
            "→",
            slot["end"]
        )