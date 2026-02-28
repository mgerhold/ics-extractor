from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Final

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore[reportMissingTypeStubs]
from googleapiclient.discovery import build  # type: ignore[reportMissingTypeStubs]

from config import Config

if TYPE_CHECKING:
    from main import Appointment

# If modifying these scopes, delete the file token.json.
SCOPES: Final = ["https://www.googleapis.com/auth/calendar.events"]


def get_google_calendar_credentials() -> Credentials | None:
    """Get Google Calendar credentials using OAuth flow."""
    creds: Credentials | None = None
    token_path: Final = Path("token.json")
    credentials_path: Final = Path("credentials.json")

    # The file token.json stores the user's access and refresh tokens
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)  # type: ignore[reportUnknownMemberType]

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:  # type: ignore[reportUnknownMemberType]
            creds.refresh(Request())  # type: ignore[reportUnknownMemberType]
        else:
            if not credentials_path.exists():
                print("\nERROR: credentials.json not found!")
                print("To enable Google Calendar upload:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Create a project or select an existing one")
                print("3. Enable Google Calendar API")
                print("4. Create OAuth 2.0 credentials (Desktop app)")
                print("5. Download the credentials.json file to this directory")
                print()
                return None

            flow: Final = InstalledAppFlow.from_client_secrets_file(  # type: ignore[reportUnknownMemberType]
                str(credentials_path), SCOPES
            )
            creds = flow.run_local_server(port=0)  # type: ignore[reportUnknownMemberType]

        # Save the credentials for the next run
        token_path.write_text(creds.to_json(), encoding="utf-8")  # type: ignore[reportUnknownMemberType]

    return creds


def upload_appointments_to_google_calendar(
    appointments: "list[Appointment]", config: Config
) -> None:
    """Upload appointments to Google Calendar."""
    print("\nAttempting to upload to Google Calendar...")

    creds: Final = get_google_calendar_credentials()
    if not creds:
        print("Skipping Google Calendar upload.")
        return

    try:
        service: Final = build("calendar", "v3", credentials=creds)  # type: ignore[reportUnknownMemberType]

        # Get events from calendar to avoid duplicates
        now: Final = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        print(f"Checking existing events in calendar '{config.google_calendar_id}'...")

        existing_events_result = service.events().list(  # type: ignore[reportUnknownMemberType]
            calendarId=config.google_calendar_id,
            timeMin=now,
            maxResults=2500,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        existing_events = existing_events_result.get("items", [])  # type: ignore[reportUnknownMemberType]
        existing_summaries: Final = {  # type: ignore[reportUnknownVariableType]
            (event.get("summary"), event.get("start", {}).get("dateTime"))  # type: ignore[reportUnknownMemberType]
            for event in existing_events  # type: ignore[reportUnknownMemberType]
        }

        uploaded_count = 0
        skipped_count = 0

        for appointment in appointments:
            # Map therapy kind to display name
            therapy_display = config.therapy_kind_mapping.get(
                appointment.therapy_kind, appointment.therapy_kind
            )

            # Create event
            start_time = appointment.date.isoformat()
            end_time = (
                appointment.date + timedelta(minutes=config.appointment_duration_minutes)
            ).isoformat()

            event_key = (therapy_display, start_time)

            # Check if event already exists
            if event_key in existing_summaries:
                skipped_count += 1
                continue

            event = {  # type: ignore[reportUnknownVariableType]
                "summary": therapy_display,
                "location": "\n".join(config.therapy_practice_address),
                "description": appointment.therapist_name,
                "start": {
                    "dateTime": start_time,
                    "timeZone": "Europe/Berlin",  # Adjust as needed
                },
                "end": {
                    "dateTime": end_time,
                    "timeZone": "Europe/Berlin",  # Adjust as needed
                },
                "status": "confirmed",
            }

            service.events().insert(  # type: ignore[reportUnknownMemberType]
                calendarId=config.google_calendar_id, body=event
            ).execute()
            uploaded_count += 1

        print(f"✓ Uploaded {uploaded_count} new appointments to Google Calendar")
        if skipped_count > 0:
            print(f"  Skipped {skipped_count} duplicate appointments")

    except Exception as e:
        print(f"ERROR uploading to Google Calendar: {e}")
