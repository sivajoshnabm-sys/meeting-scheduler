from langgraph.graph import StateGraph, END

from agent.state import MeetingState

from agent.nodes import (
    analyze_email,
    check_meeting_required,
    check_calendars,
    find_common_time,
    create_meeting,
    send_confirmation
)


def build_graph():

    workflow = StateGraph(MeetingState)

    # ----------------------------------------------------
    # Add nodes
    # ----------------------------------------------------

    workflow.add_node(
        "analyze_email",
        analyze_email
    )

    workflow.add_node(
        "check_calendars",
        check_calendars
    )

    workflow.add_node(
        "find_common_time",
        find_common_time
    )

    workflow.add_node(
        "create_meeting",
        create_meeting
    )

    workflow.add_node(
        "send_confirmation",
        send_confirmation
    )

    # ----------------------------------------------------
    # Entry point
    # ----------------------------------------------------

    workflow.set_entry_point(
        "analyze_email"
    )

    # ----------------------------------------------------
    # Check whether meeting is required
    # ----------------------------------------------------

    workflow.add_conditional_edges(
        "analyze_email",
        check_meeting_required,
        {
            "schedule": "check_calendars",
            "end": END
        }
    )

    # ----------------------------------------------------
    # Calendar checking
    # ----------------------------------------------------

    workflow.add_conditional_edges(
        "check_calendars",
        route_after_calendar_check,
        {
            "continue": "find_common_time",
            "error": END
        }
    )

    # ----------------------------------------------------
    # Find common time
    # ----------------------------------------------------

    workflow.add_conditional_edges(
    "find_common_time",
    route_after_slot_check,
    {
        "create": "create_meeting",
        "end": END
    }
)

    # ----------------------------------------------------
    # Create meeting
    # ----------------------------------------------------

    workflow.add_edge(
        "create_meeting",
        "send_confirmation"
    )

    # ----------------------------------------------------
    # Finish
    # ----------------------------------------------------

    workflow.add_edge(
        "send_confirmation",
        END
    )

    return workflow.compile()


def route_after_calendar_check(
    state: MeetingState
):

    if state.get("error"):

        print(
            "Calendar check failed. "
            "Stopping workflow."
        )

        return "error"

    return "continue"

def route_after_slot_check(
    state: MeetingState
):

    # ----------------------------------------------------
    # Error while finding common time
    # ----------------------------------------------------

    if state.get("error"):

        print(
            "Error while finding common time. "
            "Stopping workflow."
        )

        return "end"

    # ----------------------------------------------------
    # No suitable slot found
    # ----------------------------------------------------

    if not state.get("selected_slot"):

        print(
            "No suitable meeting slot found. "
            "Stopping workflow."
        )

        return "end"

    # ----------------------------------------------------
    # Slot found
    # ----------------------------------------------------

    return "create"

