from gmail_service import (
    get_recent_emails,
    get_processed_email_ids,
    mark_email_as_processed
)
from fastapi import FastAPI
from pydantic import BaseModel

from agent.graph import build_graph


app = FastAPI(
    title="AI Meeting Scheduler",
    description="Agentic AI system for automatically scheduling meetings",
    version="1.0"
)


graph = build_graph()


class ScheduleRequest(BaseModel):
    email_content: str


@app.get("/")
def root():
    return {
        "message": "AI Meeting Scheduler is running"
    }


@app.post("/agent/schedule")
def schedule_meeting(request: ScheduleRequest):

    initial_state = {
        "email_content": request.email_content
    }

    result = graph.invoke(initial_state)
    if not result.get("meeting_required", False):

        
        return {
            "status": "no_meeting_required",
            "message": "The latest email does not require a meeting.",
            "meeting_required": False,

        }

    # ----------------------------------------------------
    # Scheduling failed
    # ----------------------------------------------------

    if result.get("error"):

        return {
            "status": "failed",
            "message": result.get("status"),
            "error": result.get("error")
        }

    # ----------------------------------------------------
    # No common slot found
    # ----------------------------------------------------

    if not result.get("selected_slot"):

        return {
            "status": "no_slot_available",
            "message": "No slots found for the preferred time.",
            "meeting_required": True,
            "meeting_title": result.get("meeting_title"),
            "guest_email": result.get("guest_email"),
            "duration_minutes": result.get("duration_minutes"),
            "preferred_dates": result.get("preferred_dates"),
            "preferred_times": result.get("preferred_times")
        }

    # ----------------------------------------------------
    # Meeting successfully scheduled
    # ----------------------------------------------------

    return {
        "status": "scheduled",
        "meeting_required": True,
        "meeting_title": result.get("meeting_title"),
        "guest_email": result.get("guest_email"),
        "duration_minutes": result.get("duration_minutes"),
        "preferred_dates": result.get("preferred_dates"),
        "preferred_times": result.get("preferred_times"),
        "selected_slot": result.get("selected_slot"),
        "event_id": result.get("event_id"),
        "event_link": result.get("event_link")
    }

@app.post("/agent/schedule-latest-email")
def schedule_latest_email():

    try:
        emails = get_recent_emails(max_results=10)

        if not emails:
            return {
                "status": "no_email",
                "message": "No email found."
            }

        processed_ids = get_processed_email_ids()

        email = None

        # Find the newest unprocessed email
        for candidate in emails:
            candidate_id = candidate.get("id")

            if candidate_id not in processed_ids:
                email = candidate
                break

        if not email:
            return {
                "status": "no_new_email",
                "message": "No new unprocessed email found."
            }

        email_id = email.get("id")
        email_content = email.get("body", "")

        if not email_content:
            return {
                "status": "no_email_content",
                "message": "New email has no readable content.",
                "email_id": email_id
            }

        initial_state = {
            "email_content": email_content
        }

        result = graph.invoke(initial_state)

        # Handle workflow errors first
        if result.get("error"):
            return {
                "status": "failed",
                "message": result.get("status"),
                "error": result.get("error"),
                "email_id": email_id
            }

        # Email does not require a meeting
        if not result.get("meeting_required", False):

            mark_email_as_processed(email_id)

            return {
                "status": "no_meeting_required",
                "message": "The new email does not require a meeting.",
                "meeting_required": False,
                "email_id": email_id
            }

        # Meeting required but no slot available
        if not result.get("selected_slot"):

            return {
                "status": "no_slot_available",
                "message": "No slots found for the preferred time.",
                "meeting_required": True,
                "meeting_title": result.get("meeting_title"),
                "guest_email": result.get("guest_email"),
                "duration_minutes": result.get("duration_minutes"),
                "preferred_dates": result.get("preferred_dates"),
                "preferred_times": result.get("preferred_times"),
                "email_id": email_id
            }

        # Meeting successfully created
        mark_email_as_processed(email_id)

        return {
            "status": "scheduled",
            "meeting_required": True,
            "meeting_title": result.get("meeting_title"),
            "guest_email": result.get("guest_email"),
            "duration_minutes": result.get("duration_minutes"),
            "preferred_dates": result.get("preferred_dates"),
            "preferred_times": result.get("preferred_times"),
            "selected_slot": result.get("selected_slot"),
            "event_id": result.get("event_id"),
            "event_link": result.get("event_link"),
            "email_id": email_id
        }

    except Exception as e:

        return {
            "status": "failed",
            "message": "Unable to process new email.",
            "error": str(e)
        }