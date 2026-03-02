"""
Unit tests for calendar_api.py

Tests critical helper functions:
- parse_date_time() - Date and time parsing
- format_date_conversational() - Friendly date formatting
- format_time_conversational() - Friendly time formatting
- format_time_range() - Time range formatting
- Fuzzy matching logic in search_events()
"""

import pytest
from datetime import datetime
from freezegun import freeze_time
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calendar_api import (
    parse_date_time,
    format_time_range,
    search_events
)
from app import (
    format_date_conversational,
    format_time_conversational
)


# ==================== Tests for parse_date_time() ====================

class TestParseDatetime:
    """Test parse_date_time() function for date and time parsing."""

    @freeze_time("2026-02-28 10:00:00")
    def test_parse_today(self):
        """Test parsing 'today' returns current date at 12pm."""
        start, end = parse_date_time("today")

        assert start == "2026-02-28T12:00:00"
        assert end == "2026-02-28T13:00:00"  # Default 1 hour duration

    @freeze_time("2026-02-28 10:00:00")
    def test_parse_tomorrow(self):
        """Test parsing 'tomorrow' returns next day at 12pm."""
        start, end = parse_date_time("tomorrow")

        assert start == "2026-03-01T12:00:00"
        assert end == "2026-03-01T13:00:00"

    @freeze_time("2026-02-28 10:00:00")  # Friday
    def test_parse_day_name_monday(self):
        """Test parsing 'monday' returns next Monday."""
        start, end = parse_date_time("monday")

        # Next Monday from Friday 2026-02-28 is 2026-03-02
        assert start == "2026-03-02T12:00:00"

    @freeze_time("2026-02-28 10:00:00")  # Saturday
    def test_parse_day_name_friday(self):
        """Test parsing 'friday' returns next Friday."""
        start, end = parse_date_time("friday")

        # Current day is Saturday (2026-02-28), next Friday is 2026-03-06
        assert start == "2026-03-06T12:00:00"

    @freeze_time("2026-02-28 10:00:00")
    def test_parse_absolute_date(self):
        """Test parsing absolute date in YYYY-MM-DD format."""
        start, end = parse_date_time("2026-03-15")

        assert start == "2026-03-15T12:00:00"
        assert end == "2026-03-15T13:00:00"

    @freeze_time("2026-02-28 10:00:00")
    def test_parse_with_time_3pm(self):
        """Test parsing date with time '3pm'."""
        start, end = parse_date_time("tomorrow", "3pm")

        assert start == "2026-03-01T15:00:00"
        assert end == "2026-03-01T16:00:00"

    @freeze_time("2026-02-28 10:00:00")
    def test_parse_with_time_24hour(self):
        """Test parsing date with 24-hour time format '14:30'."""
        start, end = parse_date_time("tomorrow", "14:30")

        assert start == "2026-03-01T14:30:00"
        assert end == "2026-03-01T15:30:00"

    @freeze_time("2026-02-28 10:00:00")
    def test_parse_with_time_9am(self):
        """Test parsing date with morning time '9am'."""
        start, end = parse_date_time("today", "9am")

        assert start == "2026-02-28T09:00:00"
        assert end == "2026-02-28T10:00:00"

    @freeze_time("2026-02-28 10:00:00")
    def test_parse_with_time_12pm(self):
        """Test parsing noon (12pm edge case)."""
        start, end = parse_date_time("today", "12pm")

        assert start == "2026-02-28T12:00:00"
        assert end == "2026-02-28T13:00:00"

    @freeze_time("2026-02-28 10:00:00")
    def test_parse_with_time_12am(self):
        """Test parsing midnight (12am edge case)."""
        start, end = parse_date_time("tomorrow", "12am")

        assert start == "2026-03-01T00:00:00"
        assert end == "2026-03-01T01:00:00"

    @freeze_time("2026-02-28 10:00:00")
    def test_missing_time_defaults_to_12pm(self):
        """Test that missing time defaults to 12:00 PM."""
        start, end = parse_date_time("tomorrow")

        assert start == "2026-03-01T12:00:00"


# ==================== Tests for format_date_conversational() ====================

class TestFormatDateConversational:
    """Test format_date_conversational() function for friendly date formatting."""

    def test_first_of_month(self):
        """Test 1st gets correct ordinal suffix."""
        result = format_date_conversational("2026-03-01")
        assert result == "March 1st, 2026"

    def test_second_of_month(self):
        """Test 2nd gets correct ordinal suffix."""
        result = format_date_conversational("2026-03-02")
        assert result == "March 2nd, 2026"

    def test_third_of_month(self):
        """Test 3rd gets correct ordinal suffix."""
        result = format_date_conversational("2026-03-03")
        assert result == "March 3rd, 2026"

    def test_fourth_of_month(self):
        """Test 4th gets correct ordinal suffix."""
        result = format_date_conversational("2026-03-04")
        assert result == "March 4th, 2026"

    def test_eleventh_of_month(self):
        """Test 11th gets 'th' not 'st' (edge case)."""
        result = format_date_conversational("2026-03-11")
        assert result == "March 11th, 2026"

    def test_twelfth_of_month(self):
        """Test 12th gets 'th' not 'nd' (edge case)."""
        result = format_date_conversational("2026-03-12")
        assert result == "March 12th, 2026"

    def test_thirteenth_of_month(self):
        """Test 13th gets 'th' not 'rd' (edge case)."""
        result = format_date_conversational("2026-03-13")
        assert result == "March 13th, 2026"

    def test_twenty_first(self):
        """Test 21st gets correct ordinal suffix."""
        result = format_date_conversational("2026-03-21")
        assert result == "March 21st, 2026"

    def test_twenty_second(self):
        """Test 22nd gets correct ordinal suffix."""
        result = format_date_conversational("2026-03-22")
        assert result == "March 22nd, 2026"

    def test_thirty_first(self):
        """Test 31st gets correct ordinal suffix."""
        result = format_date_conversational("2026-03-31")
        assert result == "March 31st, 2026"

    def test_different_month(self):
        """Test formatting with different month (January)."""
        result = format_date_conversational("2026-01-15")
        assert result == "January 15th, 2026"

    def test_different_year(self):
        """Test formatting with different year."""
        result = format_date_conversational("2025-12-25")
        assert result == "December 25th, 2025"


# ==================== Tests for format_time_conversational() ====================

class TestFormatTimeConversational:
    """Test format_time_conversational() function for friendly time formatting."""

    def test_afternoon_time(self):
        """Test PM time formatting (3:00 PM)."""
        result = format_time_conversational("15:00")
        assert result == "3:00 PM"

    def test_afternoon_time_with_minutes(self):
        """Test PM time with minutes (2:30 PM)."""
        result = format_time_conversational("14:30")
        assert result == "2:30 PM"

    def test_morning_time(self):
        """Test AM time formatting (9:00 AM)."""
        result = format_time_conversational("09:00")
        assert result == "9:00 AM"

    def test_morning_time_with_minutes(self):
        """Test AM time with minutes (9:30 AM)."""
        result = format_time_conversational("09:30")
        assert result == "9:30 AM"

    def test_midnight(self):
        """Test midnight is formatted as 12:00 AM."""
        result = format_time_conversational("00:00")
        assert result == "12:00 AM"

    def test_noon(self):
        """Test noon is formatted as 12:00 PM."""
        result = format_time_conversational("12:00")
        assert result == "12:00 PM"

    def test_one_am(self):
        """Test 1:00 AM formatting."""
        result = format_time_conversational("01:00")
        assert result == "1:00 AM"

    def test_eleven_pm(self):
        """Test 11:00 PM formatting."""
        result = format_time_conversational("23:00")
        assert result == "11:00 PM"


# ==================== Tests for format_time_range() ====================

class TestFormatTimeRange:
    """Test format_time_range() function for time range formatting."""

    def test_normal_range_morning(self):
        """Test normal morning time range."""
        result = format_time_range(
            "2026-03-01T09:00:00-08:00",
            "2026-03-01T10:00:00-08:00"
        )
        assert result == "9:00 AM - 10:00 AM"

    def test_normal_range_afternoon(self):
        """Test normal afternoon time range."""
        result = format_time_range(
            "2026-03-01T14:00:00-08:00",
            "2026-03-01T15:30:00-08:00"
        )
        assert result == "2:00 PM - 3:30 PM"

    def test_range_crossing_noon(self):
        """Test time range crossing from AM to PM."""
        result = format_time_range(
            "2026-03-01T11:00:00-08:00",
            "2026-03-01T13:00:00-08:00"
        )
        assert result == "11:00 AM - 1:00 PM"

    def test_all_day_event(self):
        """Test all-day event returns 'All day'."""
        result = format_time_range(
            "2026-03-01",  # Date only, no time component
            "2026-03-02"
        )
        assert result == "All day"


# ==================== Tests for Fuzzy Matching Logic ====================

class TestFuzzyMatching:
    """Test fuzzy matching logic in search_events()."""

    @patch('calendar_api.get_calendar_service')
    @patch('calendar_api.get_user_timezone')
    def test_fuzzy_match_standup_finds_daily_standup(self, mock_timezone, mock_service):
        """Test 'standup' matches 'Daily Standup' event."""
        # Mock timezone
        mock_timezone.return_value = 'America/Los_Angeles'

        # Mock calendar service to return events
        mock_cal_service = Mock()
        mock_cal_service.events().list().execute.return_value = {
            'items': [
                {
                    'id': 'event1',
                    'summary': 'Daily Standup',
                    'start': {'dateTime': '2026-03-01T09:00:00-08:00'},
                    'end': {'dateTime': '2026-03-01T09:30:00-08:00'}
                }
            ]
        }
        mock_service.return_value = mock_cal_service

        # Search for 'standup'
        results = search_events('user123', mock_cal_service, title='standup', date_str='2026-03-01')

        # Should find the 'Daily Standup' event
        assert len(results) == 1
        assert results[0]['title'] == 'Daily Standup'

    @patch('calendar_api.get_calendar_service')
    @patch('calendar_api.get_user_timezone')
    def test_fuzzy_match_meeting_finds_team_meeting(self, mock_timezone, mock_service):
        """Test 'meeting' matches 'Team Meeting' event."""
        # Mock timezone
        mock_timezone.return_value = 'America/Los_Angeles'

        # Mock calendar service
        mock_cal_service = Mock()
        mock_cal_service.events().list().execute.return_value = {
            'items': [
                {
                    'id': 'event1',
                    'summary': 'Team Meeting',
                    'start': {'dateTime': '2026-03-01T15:00:00-08:00'},
                    'end': {'dateTime': '2026-03-01T16:00:00-08:00'}
                }
            ]
        }
        mock_service.return_value = mock_cal_service

        # Search for 'meeting'
        results = search_events('user123', mock_cal_service, title='meeting', date_str='2026-03-01')

        # Should find the 'Team Meeting' event
        assert len(results) == 1
        assert results[0]['title'] == 'Team Meeting'

    @patch('calendar_api.get_calendar_service')
    @patch('calendar_api.get_user_timezone')
    def test_fuzzy_match_dentist_finds_dentist_appointment(self, mock_timezone, mock_service):
        """Test 'dentist' matches 'Dentist Appointment' event."""
        # Mock timezone
        mock_timezone.return_value = 'America/Los_Angeles'

        # Mock calendar service
        mock_cal_service = Mock()
        mock_cal_service.events().list().execute.return_value = {
            'items': [
                {
                    'id': 'event1',
                    'summary': 'Dentist Appointment',
                    'start': {'dateTime': '2026-03-02T14:00:00-08:00'},
                    'end': {'dateTime': '2026-03-02T15:00:00-08:00'}
                }
            ]
        }
        mock_service.return_value = mock_cal_service

        # Search for 'dentist'
        results = search_events('user123', mock_cal_service, title='dentist', date_str='2026-03-02')

        # Should find the 'Dentist Appointment' event
        assert len(results) == 1
        assert results[0]['title'] == 'Dentist Appointment'

    @patch('calendar_api.get_calendar_service')
    @patch('calendar_api.get_user_timezone')
    def test_no_match_returns_empty(self, mock_timezone, mock_service):
        """Test searching for non-existent event returns empty list."""
        # Mock timezone
        mock_timezone.return_value = 'America/Los_Angeles'

        # Mock calendar service with no matching events
        mock_cal_service = Mock()
        mock_cal_service.events().list().execute.return_value = {
            'items': [
                {
                    'id': 'event1',
                    'summary': 'Team Meeting',
                    'start': {'dateTime': '2026-03-01T15:00:00-08:00'},
                    'end': {'dateTime': '2026-03-01T16:00:00-08:00'}
                }
            ]
        }
        mock_service.return_value = mock_cal_service

        # Search for something that doesn't match
        results = search_events('user123', mock_cal_service, title='nonexistent', date_str='2026-03-01')

        # Should return empty list
        assert len(results) == 0

    @patch('calendar_api.get_calendar_service')
    @patch('calendar_api.get_user_timezone')
    def test_case_insensitive_matching(self, mock_timezone, mock_service):
        """Test matching is case-insensitive."""
        # Mock timezone
        mock_timezone.return_value = 'America/Los_Angeles'

        # Mock calendar service
        mock_cal_service = Mock()
        mock_cal_service.events().list().execute.return_value = {
            'items': [
                {
                    'id': 'event1',
                    'summary': 'IMPORTANT MEETING',
                    'start': {'dateTime': '2026-03-01T15:00:00-08:00'},
                    'end': {'dateTime': '2026-03-01T16:00:00-08:00'}
                }
            ]
        }
        mock_service.return_value = mock_cal_service

        # Search with lowercase
        results = search_events('user123', mock_cal_service, title='important', date_str='2026-03-01')

        # Should find the event regardless of case
        assert len(results) == 1
        assert results[0]['title'] == 'IMPORTANT MEETING'
