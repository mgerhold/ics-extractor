import re
from datetime import datetime
from typing import Final, final

import pytest

from main import Appointment
from main import _APPOINTMENT_PATTERN  # type: ignore[reportPrivateUsage]
from main import _extract_appointments  # type: ignore[reportPrivateUsage]
from main import _match_to_appointment  # type: ignore[reportPrivateUsage]


@final
class TestAppointment:
    """Test the Appointment NamedTuple."""

    def test_appointment_creation(self) -> None:
        """Test creating an Appointment."""
        date: Final = datetime(2026, 1, 27, 16, 40)
        appointment: Final = Appointment(
            date=date, therapy_kind="KG ZNS", therapist_name="Katja"
        )
        assert appointment.date == date
        assert appointment.therapy_kind == "KG ZNS"
        assert appointment.therapist_name == "Katja"

    def test_appointment_immutable(self) -> None:
        """Test that Appointment is immutable."""
        date: Final = datetime(2026, 1, 27, 16, 40)
        appointment: Final = Appointment(
            date=date, therapy_kind="KG ZNS", therapist_name="Katja"
        )
        with pytest.raises(AttributeError):
            appointment.date = datetime(2026, 1, 28, 10, 0)  # type: ignore[misc]


@final
class TestMatchToAppointment:
    """Test the _match_to_appointment function."""

    @pytest.mark.parametrize(
        ("text", "expected_date", "expected_therapy_kind", "expected_therapist"),
        [
            pytest.param(
                "Di27.01.202616:40KG ZNS (Katja)",
                datetime(2026, 1, 27, 16, 40),
                "KG ZNS",
                "Katja",
                id="format_without_space",
            ),
            pytest.param(
                "Do 08.01.2026 14:30 O60 (Thomas)",
                datetime(2026, 1, 8, 14, 30),
                "O60",
                "Thomas",
                id="format_with_space",
            ),
        ],
    )
    def test_parse_appointment_formats(
        self,
        text: str,
        expected_date: datetime,
        expected_therapy_kind: str,
        expected_therapist: str,
    ) -> None:
        """Test parsing different appointment formats."""
        match: Final = re.search(_APPOINTMENT_PATTERN, text)
        assert match is not None
        appointment: Final = _match_to_appointment(match)
        assert appointment.date == expected_date
        assert appointment.therapy_kind == expected_therapy_kind
        assert appointment.therapist_name == expected_therapist

    @pytest.mark.parametrize(
        ("text", "expected_name"),
        [
            pytest.param("Di27.01.202616:40KG ZNS (Mike)", "Mike", id="therapist_mike"),
            pytest.param(
                "Di27.01.202616:40KG ZNS (Katja)", "Katja", id="therapist_katja"
            ),
            pytest.param(
                "Di27.01.202616:40KG ZNS (Thomas)", "Thomas", id="therapist_thomas"
            ),
            pytest.param(
                "Di27.01.202616:40KG ZNS (Dr. Smith)",
                "Dr. Smith",
                id="therapist_with_title",
            ),
        ],
    )
    def test_different_therapist_names(self, text: str, expected_name: str) -> None:
        """Test different therapist names."""
        match: Final = re.search(_APPOINTMENT_PATTERN, text)
        assert match is not None
        appointment: Final = _match_to_appointment(match)
        assert appointment.therapist_name == expected_name

    @pytest.mark.parametrize(
        ("text", "expected_date"),
        [
            pytest.param(
                "Di27.01.202616:40KG ZNS (Katja)",
                datetime(2026, 1, 27, 16, 40),
                id="time_16_40",
            ),
            pytest.param(
                "Di27.01.202617:10KG ZNS (Katja)",
                datetime(2026, 1, 27, 17, 10),
                id="time_17_10",
            ),
            pytest.param(
                "Di27.01.202609:00KG ZNS (Katja)",
                datetime(2026, 1, 27, 9, 0),
                id="time_09_00",
            ),
            pytest.param(
                "Di27.01.202623:59KG ZNS (Katja)",
                datetime(2026, 1, 27, 23, 59),
                id="time_23_59",
            ),
        ],
    )
    def test_different_times(self, text: str, expected_date: datetime) -> None:
        """Test different time formats."""
        match: Final = re.search(_APPOINTMENT_PATTERN, text)
        assert match is not None
        appointment: Final = _match_to_appointment(match)
        assert appointment.date == expected_date

    @pytest.mark.parametrize(
        ("text", "expected_therapy_kind"),
        [
            pytest.param("Di27.01.202616:40KG ZNS (Katja)", "KG ZNS", id="kg_zns"),
            pytest.param("Do 08.01.2026 14:30 O60 (Thomas)", "O60", id="o60"),
            pytest.param("Di27.01.202616:40MT (Mike)", "MT", id="mt"),
            pytest.param("Di27.01.202616:40Massage (Anna)", "Massage", id="massage"),
        ],
    )
    def test_different_therapy_kinds(
        self, text: str, expected_therapy_kind: str
    ) -> None:
        """Test different therapy kinds."""
        match: Final = re.search(_APPOINTMENT_PATTERN, text)
        assert match is not None
        appointment: Final = _match_to_appointment(match)
        assert appointment.therapy_kind == expected_therapy_kind

    def test_whitespace_in_therapist_name(self) -> None:
        """Test that whitespace is stripped from therapist name."""
        text: Final = "Di27.01.202616:40KG ZNS (  Katja  )"
        match: Final = re.search(_APPOINTMENT_PATTERN, text)
        assert match is not None
        appointment: Final = _match_to_appointment(match)
        assert appointment.therapist_name == "Katja"


@final
class TestExtractAppointments:
    """Test the _extract_appointments function."""

    def test_empty_text(self) -> None:
        """Test extracting from empty text."""
        appointments: Final = _extract_appointments("")
        assert appointments == []

    def test_text_without_appointments(self) -> None:
        """Test extracting from text without appointments."""
        text: Final = "This is some random text without any appointments."
        appointments: Final = _extract_appointments(text)
        assert appointments == []

    def test_single_appointment(self) -> None:
        """Test extracting a single appointment."""
        text: Final = "Di27.01.202616:40KG ZNS (Katja)"
        appointments: Final = _extract_appointments(text)
        assert len(appointments) == 1
        assert appointments[0].date == datetime(2026, 1, 27, 16, 40)
        assert appointments[0].therapist_name == "Katja"

    def test_multiple_appointments(self) -> None:
        """Test extracting multiple appointments."""
        text: Final = """
        Di27.01.202616:40KG ZNS (Katja)
        Di27.01.202617:10KG ZNS (Katja)
        Do29.01.202615:30KG ZNS (Mike)
        Do29.01.202616:00KG ZNS (Mike)
        """
        appointments: Final = _extract_appointments(text)
        assert len(appointments) == 4
        assert appointments[0].date == datetime(2026, 1, 27, 16, 40)
        assert appointments[0].therapist_name == "Katja"
        assert appointments[1].date == datetime(2026, 1, 27, 17, 10)
        assert appointments[1].therapist_name == "Katja"
        assert appointments[2].date == datetime(2026, 1, 29, 15, 30)
        assert appointments[2].therapist_name == "Mike"
        assert appointments[3].date == datetime(2026, 1, 29, 16, 0)
        assert appointments[3].therapist_name == "Mike"

    def test_mixed_format_appointments(self) -> None:
        """Test extracting appointments with mixed formats (with and without space)."""
        text: Final = """
        Di27.01.202616:40KG ZNS (Katja)
        Do 08.01.2026 14:30 O60 (Thomas)
        Do29.01.202615:30KG ZNS (Mike)
        """
        appointments: Final = _extract_appointments(text)
        assert len(appointments) == 3
        assert appointments[0].date == datetime(2026, 1, 27, 16, 40)
        assert appointments[0].therapist_name == "Katja"
        assert appointments[1].date == datetime(2026, 1, 8, 14, 30)
        assert appointments[1].therapist_name == "Thomas"
        assert appointments[2].date == datetime(2026, 1, 29, 15, 30)
        assert appointments[2].therapist_name == "Mike"

    def test_appointments_with_surrounding_text(self) -> None:
        """Test extracting appointments from text with surrounding content."""
        text: Final = """
        rehalife GmbH
        Schloßstraße 110
        12163 Berlin
        
        Behandlungstermine für das Rezept vom 08.02.2023
        
        Di27.01.202616:40KG ZNS (Katja)
        Di27.01.202617:10KG ZNS (Katja)
        
        Terminabsage: Bitte sagen Sie Termine ab.
        """
        appointments: Final = _extract_appointments(text)
        assert len(appointments) == 2
        assert appointments[0].date == datetime(2026, 1, 27, 16, 40)
        assert appointments[1].date == datetime(2026, 1, 27, 17, 10)

    def test_appointments_in_different_months(self) -> None:
        """Test appointments spanning multiple months."""
        text: Final = """
        Di27.01.202616:40KG ZNS (Katja)
        Di03.02.202616:40KG ZNS (Katja)
        Di03.03.202616:40KG ZNS (Mike)
        Di07.04.202616:40KG ZNS (Thomas)
        """
        appointments: Final = _extract_appointments(text)
        assert len(appointments) == 4
        assert appointments[0].date.month == 1
        assert appointments[1].date.month == 2
        assert appointments[2].date.month == 3
        assert appointments[3].date.month == 4

    def test_appointments_sorted_by_occurrence(self) -> None:
        """Test that appointments are returned in order of occurrence."""
        text: Final = """
        Do29.01.202615:30KG ZNS (Mike)
        Di27.01.202616:40KG ZNS (Katja)
        Di03.02.202616:40KG ZNS (Katja)
        """
        appointments: Final = _extract_appointments(text)
        # Order should match text order, not date order
        assert appointments[0].date == datetime(2026, 1, 29, 15, 30)
        assert appointments[1].date == datetime(2026, 1, 27, 16, 40)
        assert appointments[2].date == datetime(2026, 2, 3, 16, 40)

    def test_different_treatment_codes(self) -> None:
        """Test appointments with different treatment codes."""
        text: Final = """
        Di27.01.202616:40KG ZNS (Katja)
        Do 08.01.2026 14:30 O60 (Thomas)
        Di27.01.202616:40MT (Mike)
        Di27.01.202616:40Massage (Anna)
        """
        appointments: Final = _extract_appointments(text)
        assert len(appointments) == 4
        # All should be extracted regardless of treatment code
        assert all(isinstance(apt, Appointment) for apt in appointments)


@final
class TestAppointmentPattern:
    """Test the regex pattern for appointments."""

    @pytest.mark.parametrize(
        "text",
        [
            pytest.param("Di27.01.202616:40KG ZNS (Katja)", id="standard_format"),
            pytest.param("Do 08.01.2026 14:30 O60 (Thomas)", id="format_with_space"),
        ],
    )
    def test_pattern_matches_valid_formats(self, text: str) -> None:
        """Test that pattern matches valid formats."""
        match: Final = re.search(_APPOINTMENT_PATTERN, text)
        assert match is not None

    @pytest.mark.parametrize(
        ("text", "reason"),
        [
            pytest.param(
                "27.01.2026 16:40 (Katja)",
                "missing_day_abbreviation",
                id="missing_day_abbreviation",
            ),
            pytest.param("Di27.01.2026 (Katja)", "missing_time", id="missing_time"),
            pytest.param(
                "Di27.01.202616:40 Katja",
                "missing_parentheses",
                id="missing_parentheses",
            ),
            pytest.param(
                "27/01/2026 16:40 (Katja)",
                "wrong_date_separator_slash",
                id="wrong_date_separator_slash",
            ),
            pytest.param(
                "Di27-01-202616:40 (Katja)",
                "wrong_date_separator_dash",
                id="wrong_date_separator_dash",
            ),
        ],
    )
    def test_pattern_does_not_match_invalid_format(
        self, text: str, reason: str
    ) -> None:
        """Test that pattern does not match invalid formats."""
        match: Final = re.search(_APPOINTMENT_PATTERN, text)
        assert match is None, f"Pattern should not match ({reason}): {text}"

    def test_pattern_extracts_correct_groups(self) -> None:
        """Test that pattern extracts the correct groups."""
        text: Final = "Di27.01.202616:40KG ZNS (Katja)"
        match: Final = re.search(_APPOINTMENT_PATTERN, text)
        assert match is not None
        assert match.group(1) == "27.01.2026"  # Date
        assert match.group(2) == "16:40"  # Time
        assert match.group(3) == "KG ZNS"  # Therapy kind
        assert match.group(4) == "Katja"  # Therapist name
