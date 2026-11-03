from availability import (
    calculate_available_slots,
    find_common_slots
)


if __name__ == "__main__":

    host_busy = [
        {
            "start": "2026-09-28T11:00:00+05:30",
            "end": "2026-09-28T12:00:00+05:30"
        }
    ]

    guest_busy = [
        {
            "start": "2026-09-28T10:00:00+05:30",
            "end": "2026-09-28T10:30:00+05:30"
        },
        {
            "start": "2026-09-28T14:00:00+05:30",
            "end": "2026-09-28T15:00:00+05:30"
        }
    ]

    host_slots = calculate_available_slots(
        busy_periods=host_busy,
        start_time="2026-09-28T09:00:00+05:30",
        end_time="2026-09-28T18:00:00+05:30",
        duration_minutes=30
    )

    guest_slots = calculate_available_slots(
        busy_periods=guest_busy,
        start_time="2026-09-28T09:00:00+05:30",
        end_time="2026-09-28T18:00:00+05:30",
        duration_minutes=30
    )

    common_slots = find_common_slots(
        host_slots,
        guest_slots
    )

    print("\nCommon available slots:\n")

    for slot in common_slots:
        print(
            slot["start"],
            "→",
            slot["end"]
        )