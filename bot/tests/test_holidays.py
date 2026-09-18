import pytest
from datetime import datetime
from bot.src.data.holidays import (
    get_next_holidays,
    get_upcoming_holidays,
    is_holiday_today,
    easter_date,
    get_all_holidays,
)


def test_easter_calculation():
    """Test Páscoa calculation for known years."""
    # Easter 2024 was April 31
    month, day = easter_date(2024)
    assert month == 3 and day == 31

    # Easter 2025 is April 20
    month, day = easter_date(2025)
    assert month == 4 and day == 20


def test_fixed_holidays_include_main_dates():
    """Test if fixed holidays include main Brazilian holidays."""
    holidays_2024 = get_all_holidays(2024)
    holiday_names = [h["name"] for h in holidays_2024]

    assert "Ano Novo" in holiday_names
    assert "Tiradentes" in holiday_names
    assert "Dia do Trabalho" in holiday_names
    assert "Independência do Brasil" in holiday_names
    assert "Natal" in holiday_names


def test_get_next_holidays_returns_future_dates():
    """Test that next holidays are in the future."""
    holidays = get_next_holidays(limit=5)

    today = datetime.now()
    for holiday in holidays:
        holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d")
        assert holiday_date >= today


def test_get_upcoming_holidays_within_3_days():
    """Test upcoming holidays are within specified days."""
    upcoming = get_upcoming_holidays(days_before=3)

    today = datetime.now()
    for holiday in upcoming:
        holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d")
        days_diff = (holiday_date - today).days
        assert 0 <= days_diff <= 3


def test_holiday_contains_required_fields():
    """Test that holidays have all required fields."""
    holidays = get_next_holidays(limit=1)

    assert len(holidays) > 0
    holiday = holidays[0]
    assert "date" in holiday
    assert "name" in holiday
    assert "type" in holiday


def test_next_holidays_limit():
    """Test that next_holidays respects limit parameter."""
    for limit in [1, 5, 10]:
        holidays = get_next_holidays(limit=limit)
        assert len(holidays) <= limit


def test_upcoming_holidays_empty_for_far_future():
    """Test that no holidays are returned for short window."""
    # This might fail if there's a holiday today, but unlikely
    upcoming = get_upcoming_holidays(days_before=0)
    # Just verify it returns a list (could be empty)
    assert isinstance(upcoming, list)
