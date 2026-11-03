from gmail_service import get_recent_emails


if __name__ == "__main__":

    emails = get_recent_emails(max_results=5)

    print("\nRecent emails:\n")

    for email in emails:

        print("--------------------------------")
        print("ID:", email["id"])
        print("From:", email["from"])
        print("Subject:", email["subject"])
        print("Date:", email["date"])

        print("\nEmail Body:")
        print(email["body"])

        print("--------------------------------")