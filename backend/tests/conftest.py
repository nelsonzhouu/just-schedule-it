"""
Shared pytest fixtures for backend tests.

Provides common test fixtures used across multiple test files:
- Mocked Google Calendar service
- Mocked Groq client
- Sample event data
- Time freezing
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from freezegun import freeze_time


@pytest.fixture
def mock_google_service():
    """
    Mock Google Calendar service object.

    Returns a configured mock that simulates Google Calendar API responses.
    Used for testing calendar operations without making real API calls.
    """
    service = Mock()

    # Mock events().list() chain
    events_list = MagicMock()
    events_list.list.return_value.execute.return_value = {
        'items': [
            {
                'id': 'event123',
                'summary': 'Team Meeting',
                'start': {'dateTime': '2026-03-01T15:00:00-08:00'},
                'end': {'dateTime': '2026-03-01T16:00:00-08:00'}
            },
            {
                'id': 'event456',
                'summary': 'Daily Standup',
                'start': {'dateTime': '2026-03-01T09:00:00-08:00'},
                'end': {'dateTime': '2026-03-01T09:30:00-08:00'}
            }
        ]
    }
    service.events.return_value = events_list

    # Mock settings().get() chain for timezone
    settings_mock = MagicMock()
    settings_mock.get.return_value.execute.return_value = {
        'value': 'America/Los_Angeles'
    }
    service.settings.return_value = settings_mock

    return service


@pytest.fixture
def sample_events():
    """
    Sample event data for testing.

    Returns a list of event dictionaries matching Google Calendar API format.
    """
    return [
        {
            'id': 'event1',
            'summary': 'Team Meeting',
            'start': {'dateTime': '2026-03-01T15:00:00-08:00'},
            'end': {'dateTime': '2026-03-01T16:00:00-08:00'}
        },
        {
            'id': 'event2',
            'summary': 'Daily Standup',
            'start': {'dateTime': '2026-03-01T09:00:00-08:00'},
            'end': {'dateTime': '2026-03-01T09:30:00-08:00'}
        },
        {
            'id': 'event3',
            'summary': 'Dentist Appointment',
            'start': {'dateTime': '2026-03-02T14:00:00-08:00'},
            'end': {'dateTime': '2026-03-02T15:00:00-08:00'}
        }
    ]


@pytest.fixture
def frozen_time():
    """
    Freeze time at 2026-02-28 10:00:00 for deterministic date tests.

    This makes date parsing predictable:
    - "today" = 2026-02-28
    - "tomorrow" = 2026-03-01
    - Current weekday = Friday
    """
    with freeze_time("2026-02-28 10:00:00"):
        yield
