import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.freebusy",
    "https://www.googleapis.com/auth/calendar.events"
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CREDENTIALS_FILE = os.path.join(
    BASE_DIR,
    "data",
    "credentials",
    "credentials.json"
)

TOKEN_FILE = os.path.join(
    BASE_DIR,
    "data",
    "credentials",
    "token.json"
)


def get_google_credentials():
    credentials = None

    # Check whether we already have a saved login
    if os.path.exists(TOKEN_FILE):
        credentials = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    # Refresh expired credentials
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    # First-time login
    if not credentials or not credentials.valid:

        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            SCOPES
        )

        credentials = flow.run_local_server(port=0)

        # Save login token
        with open(TOKEN_FILE, "w") as token:
            token.write(credentials.to_json())

    return credentials