from google_auth import get_google_credentials


if __name__ == "__main__":
    credentials = get_google_credentials()

    if credentials and credentials.valid:
        print("Google authentication successful!")
    else:
        print("Google authentication failed.")