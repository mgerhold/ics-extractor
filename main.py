import re
from datetime import datetime
from pathlib import Path
from typing import Final, NamedTuple, final
from pypdf import PdfReader


_INPUT_PATH = Path(__file__).parent / "input"
_OUTPUT_PATH = Path(__file__).parent / "output"


@final
class Appointment(NamedTuple):
    date: datetime
    therapist_name: str


def main() -> None:
    _OUTPUT_PATH.mkdir(exist_ok=True)
    for input_file in _INPUT_PATH.glob("*.pdf"):
        _process_pdf(input_file)


def _process_pdf(input_file: Path) -> None:
    reader: Final = PdfReader(input_file)
    text: Final = "\n".join(page.extract_text() for page in reader.pages)

    appointments: Final = _extract_appointments(text)
    print(f"Found {len(appointments)} appointments:")
    for appointment in appointments:
        print(
            f"  {appointment.date.strftime('%Y-%m-%d %H:%M')} - {appointment.therapist_name}"
        )


# Pattern: DayAbbrev DD.MM.YYYY HH:MM Treatment (TherapistName)
# Example: Di27.01.202616:40KG ZNS (Katja)
_APPOINTMENT_PATTERN = r"[A-Za-z]{2}(\d{2}\.\d{2}\.\d{4})(\d{2}:\d{2})[^(]+\(([^)]+)\)"


def _extract_appointments(text: str) -> list[Appointment]:
    """Extract appointments from PDF text."""

    return [
        _match_to_appointment(match)
        for match in re.finditer(_APPOINTMENT_PATTERN, text)
    ]


def _match_to_appointment(match: re.Match[str]) -> Appointment:
    date_str: Final = match.group(1)  # DD.MM.YYYY
    time_str: Final = match.group(2)  # HH:MM
    therapist_name: Final = match.group(3).strip()

    datetime_str: Final = f"{date_str} {time_str}"
    date: Final = datetime.strptime(datetime_str, "%d.%m.%Y %H:%M")
    return Appointment(date=date, therapist_name=therapist_name)


if __name__ == "__main__":
    main()
