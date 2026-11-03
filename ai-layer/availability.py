from datetime import datetime, timedelta


# ============================================================
# 1. CALCULATE AVAILABLE SLOTS
# ============================================================

def calculate_available_slots(
    busy_periods,
    start_time,
    end_time,
    duration_minutes=30
):

    start = datetime.fromisoformat(
        start_time
    )

    end = datetime.fromisoformat(
        end_time
    )

    duration = timedelta(
        minutes=duration_minutes
    )

    busy = []

    for period in busy_periods:

        busy_start = datetime.fromisoformat(
            period["start"]
        )

        busy_end = datetime.fromisoformat(
            period["end"]
        )

        busy.append(
            (
                busy_start,
                busy_end
            )
        )

    busy.sort(
        key=lambda x: x[0]
    )

    available_slots = []

    current_time = start

    for busy_start, busy_end in busy:

        while current_time + duration <= busy_start:

            slot_end = (
                current_time + duration
            )

            available_slots.append(
                {
                    "start": current_time.isoformat(),
                    "end": slot_end.isoformat()
                }
            )

            current_time = slot_end

        if busy_end > current_time:

            current_time = busy_end

    while current_time + duration <= end:

        slot_end = (
            current_time + duration
        )

        available_slots.append(
            {
                "start": current_time.isoformat(),
                "end": slot_end.isoformat()
            }
        )

        current_time = slot_end

    return available_slots


# ============================================================
# 2. FIND COMMON AVAILABLE SLOTS
# ============================================================

def find_common_slots(
    host_busy,
    guest_busy,
    start_time,
    end_time,
    duration_minutes=30
):

    start = datetime.fromisoformat(
        start_time
    )

    end = datetime.fromisoformat(
        end_time
    )

    duration = timedelta(
        minutes=duration_minutes
    )

    # --------------------------------------------------------
    # Convert host busy periods into datetime objects
    # --------------------------------------------------------

    host_busy_periods = []

    for period in host_busy:

        busy_start = datetime.fromisoformat(
            period["start"]
        )

        busy_end = datetime.fromisoformat(
            period["end"]
        )

        host_busy_periods.append(
            (
                busy_start,
                busy_end
            )
        )

    # --------------------------------------------------------
    # Convert guest busy periods into datetime objects
    # --------------------------------------------------------

    guest_busy_periods = []

    for period in guest_busy:

        busy_start = datetime.fromisoformat(
            period["start"]
        )

        busy_end = datetime.fromisoformat(
            period["end"]
        )

        guest_busy_periods.append(
            (
                busy_start,
                busy_end
            )
        )

    # Sort busy periods
    host_busy_periods.sort(
        key=lambda x: x[0]
    )

    guest_busy_periods.sort(
        key=lambda x: x[0]
    )

    # --------------------------------------------------------
    # Find common free slots
    # --------------------------------------------------------

    common_slots = []

    current_time = start

    while current_time + duration <= end:

        slot_end = (
            current_time + duration
        )

        # ----------------------------------------------------
        # Check whether host is busy
        # ----------------------------------------------------

        host_is_busy = False

        for busy_start, busy_end in host_busy_periods:

            if (
                current_time < busy_end
                and slot_end > busy_start
            ):

                host_is_busy = True
                break

        # ----------------------------------------------------
        # Check whether guest is busy
        # ----------------------------------------------------

        guest_is_busy = False

        for busy_start, busy_end in guest_busy_periods:

            if (
                current_time < busy_end
                and slot_end > busy_start
            ):

                guest_is_busy = True
                break

        # ----------------------------------------------------
        # If both are free, this is a common slot
        # ----------------------------------------------------

        if not host_is_busy and not guest_is_busy:

            common_slots.append(
                {
                    "start": current_time.isoformat(),
                    "end": slot_end.isoformat()
                }
            )

        # Move to the next possible slot
        current_time = slot_end

    return common_slots