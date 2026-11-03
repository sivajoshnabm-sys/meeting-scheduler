from availability import find_common_slots


host_busy = [
    {
        "start": "2026-09-30T09:00:00+05:30",
        "end": "2026-09-30T18:00:00+05:30"
    }
]

guest_busy = [
    {
        "start": "2026-09-30T09:00:00+05:30",
        "end": "2026-09-30T18:00:00+05:30"
    }
]


common_slots = find_common_slots(
    host_busy=host_busy,
    guest_busy=guest_busy,
    start_time="2026-09-30T09:00:00+05:30",
    end_time="2026-09-30T18:00:00+05:30",
    duration_minutes=30
)


print("Common slots:")
print(common_slots)

if not common_slots:
    print("TEST F PASSED")
    print("No common availability found.")
else:
    print("TEST F FAILED")
    print("Common slots were found:", common_slots)