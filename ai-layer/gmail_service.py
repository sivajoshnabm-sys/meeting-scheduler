import os
import json
import base64

from googleapiclient.discovery import build

from google_auth import get_google_credentials


def get_gmail_service():

    credentials = get_google_credentials()

    service = build(
        "gmail",
        "v1",
        credentials=credentials
    )

    return service


def decode_body(data):

    decoded_bytes = base64.urlsafe_b64decode(
        data + "=" * (-len(data) % 4)
    )

    return decoded_bytes.decode(
        "utf-8",
        errors="ignore"
    )


def extract_email_body(payload):

    # Simple email body
    if payload.get("body", {}).get("data"):

        return decode_body(
            payload["body"]["data"]
        )

    # Multipart email
    parts = payload.get("parts", [])

    for part in parts:

        mime_type = part.get("mimeType", "")

        if mime_type == "text/plain":

            body_data = part.get(
                "body",
                {}
            ).get("data")

            if body_data:

                return decode_body(
                    body_data
                )

        # Check nested multipart sections
        if part.get("parts"):

            body = extract_email_body(part)

            if body:

                return body

    return ""


def get_recent_emails(max_results=5):

    service = get_gmail_service()

    # Search Inbox + Spam.
    # Exclude Trash.
    query = "{in:inbox in:spam} -in:trash"

    response = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_results
    ).execute()

    messages = response.get(
        "messages",
        []
    )

    emails = []

    for message in messages:

        message_id = message["id"]

        email_data = service.users().messages().get(
            userId="me",
            id=message_id,
            format="full"
        ).execute()

        payload = email_data.get(
            "payload",
            {}
        )

        headers = payload.get(
            "headers",
            []
        )

        subject = ""
        sender = ""
        recipient = ""
        date = ""

        for header in headers:

            name = header.get(
                "name",
                ""
            ).lower()

            value = header.get(
                "value",
                ""
            )

            if name == "subject":
                subject = value

            elif name == "from":
                sender = value

            elif name == "to":
                recipient = value

            elif name == "date":
                date = value

        body = extract_email_body(
            payload
        )

        labels = email_data.get(
            "labelIds",
            []
        )

        emails.append(
            {
                "id": message_id,
                "thread_id": email_data.get(
                    "threadId"
                ),
                "subject": subject,
                "from": sender,
                "to": recipient,
                "date": date,
                "body": body,
                "labels": labels
            }
        )

    return emails


def get_latest_email():

    emails = get_recent_emails(
        max_results=10
    )

    if not emails:

        return None

    return emails[0]


def get_processed_email_ids():

    file_path = os.path.join(
        os.path.dirname(
            os.path.dirname(__file__)
        ),
        "data",
        "processed_emails.json"
    )

    if not os.path.exists(file_path):

        return []

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    return data.get(
        "processed_ids",
        []
    )


def mark_email_as_processed(message_id):

    file_path = os.path.join(
        os.path.dirname(
            os.path.dirname(__file__)
        ),
        "data",
        "processed_emails.json"
    )

    processed_ids = get_processed_email_ids()

    if message_id not in processed_ids:

        processed_ids.append(
            message_id
        )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            {
                "processed_ids": processed_ids
            },
            file,
            indent=4
        )