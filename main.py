import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Final, NamedTuple, final

from icalendar import Calendar, Event
from pypdf import PdfReader

from config import Config
from google_calendar import upload_appointments_to_google_calendar


def _get_base_path() -> Path:
    """Get the base directory for the application.
    
    When running as a PyInstaller bundle, use the directory containing the .exe.
    Otherwise, use the directory containing this script.
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return Path(sys.executable).parent
    else:
        # Running as script
        return Path(__file__).parent


_INPUT_PATH = _get_base_path() / "input"
_OUTPUT_PATH = _get_base_path() / "output"
_CONFIG_PATH = _get_base_path() / "config.json"


@final
class Appointment(NamedTuple):
    date: datetime
    therapy_kind: str
    therapist_name: str


def main() -> None:
    _INPUT_PATH.mkdir(exist_ok=True)
    _OUTPUT_PATH.mkdir(exist_ok=True)
    config: Final = Config.load_or_default(_CONFIG_PATH)
    for input_file in _INPUT_PATH.glob("*.pdf"):
        _process_pdf(input_file, config)


def _process_pdf(input_file: Path, config: Config) -> None:
    reader: Final = PdfReader(input_file)
    text: Final = "\n".join(page.extract_text() for page in reader.pages)

    appointments: Final = _extract_appointments(text)
    print(f"Found {len(appointments)} appointments:")
    for appointment in appointments:
        print(
            f"  {appointment.date.strftime('%Y-%m-%d %H:%M')} - {appointment.therapy_kind} - {appointment.therapist_name}"
        )

    # Generate ICS file
    ics_content: Final = _generate_ics(appointments, config)
    output_file: Final = _OUTPUT_PATH / f"{input_file.stem}.ics"
    output_file.write_bytes(ics_content)
    print(f"\nGenerated ICS file: {output_file}")

    # Upload to Google Calendar if enabled
    if config.enable_google_calendar_upload:
        upload_appointments_to_google_calendar(appointments, config)


# Pattern: DayAbbrev DD.MM.YYYY HH:MM Treatment (TherapistName)
# Example: Di27.01.202616:40KG ZNS (Katja) or Do 08.01.2026 14:30 O60 (Thomas)
_APPOINTMENT_PATTERN = (
    r"[A-Za-z]{2}\s*(\d{2}\.\d{2}\.\d{4})\s*(\d{2}:\d{2})\s*([^(]+?)\s*\(([^)]+)\)"
)


def _extract_appointments(text: str) -> list[Appointment]:
    """Extract appointments from PDF text."""

    return [
        _match_to_appointment(match)
        for match in re.finditer(_APPOINTMENT_PATTERN, text)
    ]


def _match_to_appointment(match: re.Match[str]) -> Appointment:
    date_str: Final = match.group(1)  # DD.MM.YYYY
    time_str: Final = match.group(2)  # HH:MM
    therapy_kind: Final = match.group(3).strip()  # Therapy kind
    therapist_name: Final = match.group(4).strip()  # Therapist name

    datetime_str: Final = f"{date_str} {time_str}"
    date: Final = datetime.strptime(datetime_str, "%d.%m.%Y %H:%M")
    return Appointment(date=date, therapy_kind=therapy_kind, therapist_name=therapist_name)


def _generate_ics(appointments: list[Appointment], config: Config) -> bytes:
    """Generate ICS (iCalendar) content from appointments."""
    calendar: Final = Calendar()
    calendar.add("prodid", "-//ICS Extractor//EN")  # type: ignore[reportUnknownMemberType]
    calendar.add("version", "2.0")  # type: ignore[reportUnknownMemberType]

    for idx, appointment in enumerate(appointments, start=1):
        event = _create_event(appointment, idx, config)
        calendar.add_component(event)

    return calendar.to_ical()


def _create_event(appointment: Appointment, event_id: int, config: Config) -> Event:
    """Create an iCalendar event from an appointment."""
    event: Final = Event()

    # Get appointment duration from config
    duration: Final = timedelta(minutes=config.appointment_duration_minutes)
    end_time: Final = appointment.date + duration

    # Create unique ID
    uid: Final = f"{appointment.date.strftime('%Y%m%d%H%M%S')}-{event_id}@ics-extractor"

    # Map therapy kind to display name
    therapy_display: Final = config.therapy_kind_mapping.get(
        appointment.therapy_kind, appointment.therapy_kind
    )

    # Location from config
    location: Final = "\n".join(config.therapy_practice_address)

    event.add("uid", uid)  # type: ignore[reportUnknownMemberType]
    event.add("dtstamp", datetime.now())  # type: ignore[reportUnknownMemberType]
    event.add("dtstart", appointment.date)  # type: ignore[reportUnknownMemberType]
    event.add("dtend", end_time)  # type: ignore[reportUnknownMemberType]
    event.add("summary", therapy_display)  # type: ignore[reportUnknownMemberType]
    event.add("description", appointment.therapist_name)  # type: ignore[reportUnknownMemberType]
    event.add("location", location)  # type: ignore[reportUnknownMemberType]
    event.add("status", "CONFIRMED")  # type: ignore[reportUnknownMemberType]

    return event


if __name__ == "__main__":
    main()
