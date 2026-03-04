"""
Unit tests for app.py

Tests the /api/message endpoint with Groq parsing:
- Notes parsing
- Reminders parsing
- update_note action handling
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app


# ==================== Test Fixtures ====================

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=False)
def mock_auth(client):
    """Mock authentication by patching verify_jwt to return a test user_id."""
    # Patch verify_jwt in the auth module to always return our test user_id
    with patch('auth.verify_jwt', return_value='user123'):
        # Set a dummy JWT cookie so require_auth doesn't reject immediately
        client.set_cookie('jwt_token', 'test_token')
        yield


# ==================== Tests for Groq Parsing - Notes ====================

class TestGroqParsingNotes:
    """Test Groq parsing of notes in /api/message endpoint."""

    @patch('app.create_event')
    @patch('app.groq_client')
    def test_parse_note_bring_laptop(self, mock_groq, mock_create_event, client, mock_auth):
        """Test 'note: bring laptop' gets parsed into note field."""
        # Mock Groq response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "action": "create",
            "title": "meeting",
            "date": "2026-03-01",
            "time": "15:00",
            "end_time": None,
            "new_date": None,
            "new_time": None,
            "new_end_time": None,
            "note": "bring laptop",
            "reminder_minutes": None,
            "confidence": 0.95
        })
        mock_groq.chat.completions.create.return_value = mock_response

        # Mock create_event success response
        mock_create_event.return_value = {
            'success': True,
            'message': 'Event created',
            'event': {
                'id': 'event123',
                'title': 'Meeting',
                'start': '2026-03-01T15:00:00',
                'end': '2026-03-01T16:00:00',
                'reminder_minutes': 30
            }
        }

        # Send request
        response = client.post('/api/message', json={
            'message': 'schedule a meeting tomorrow at 3pm, note: bring laptop'
        })

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Verify create_event was called with note
        mock_create_event.assert_called_once()
        call_args = mock_create_event.call_args[0]
        parsed_data = call_args[1]
        assert parsed_data['note'] == 'bring laptop'


# ==================== Tests for Groq Parsing - Reminders ====================

class TestGroqParsingReminders:
    """Test Groq parsing of reminders in /api/message endpoint."""

    @patch('app.create_event')
    @patch('app.groq_client')
    def test_parse_remind_1_hour_before(self, mock_groq, mock_create_event, client, mock_auth):
        """Test 'remind me 1 hour before' gets parsed into reminder_minutes: 60."""
        # Mock Groq response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "action": "create",
            "title": "dentist appointment",
            "date": "2026-03-01",
            "time": "14:00",
            "end_time": None,
            "new_date": None,
            "new_time": None,
            "new_end_time": None,
            "note": None,
            "reminder_minutes": 60,
            "confidence": 0.90
        })
        mock_groq.chat.completions.create.return_value = mock_response

        # Mock create_event success response
        mock_create_event.return_value = {
            'success': True,
            'message': 'Event created',
            'event': {
                'id': 'event123',
                'title': 'Dentist Appointment',
                'start': '2026-03-01T14:00:00',
                'end': '2026-03-01T15:00:00',
                'reminder_minutes': 60
            }
        }

        # Send request
        response = client.post('/api/message', json={
            'message': 'remind me 1 hour before my dentist appointment tomorrow at 2pm'
        })

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Verify create_event was called with 60 minute reminder
        mock_create_event.assert_called_once()
        call_args = mock_create_event.call_args[0]
        parsed_data = call_args[1]
        assert parsed_data['reminder_minutes'] == 60

    @patch('app.create_event')
    @patch('app.groq_client')
    def test_parse_no_reminder(self, mock_groq, mock_create_event, client, mock_auth):
        """Test 'no reminder' gets parsed into reminder_minutes: null."""
        # Mock Groq response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "action": "create",
            "title": "meeting",
            "date": "2026-03-05",
            "time": "16:00",
            "end_time": None,
            "new_date": None,
            "new_time": None,
            "new_end_time": None,
            "note": None,
            "reminder_minutes": None,
            "confidence": 0.90
        })
        mock_groq.chat.completions.create.return_value = mock_response

        # Mock create_event success response
        mock_create_event.return_value = {
            'success': True,
            'message': 'Event created',
            'event': {
                'id': 'event123',
                'title': 'Meeting',
                'start': '2026-03-05T16:00:00',
                'end': '2026-03-05T17:00:00',
                'reminder_minutes': None
            }
        }

        # Send request
        response = client.post('/api/message', json={
                'message': 'schedule a meeting Friday at 4pm without a reminder'
            })

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Verify create_event was called with null reminder
        mock_create_event.assert_called_once()
        call_args = mock_create_event.call_args[0]
        parsed_data = call_args[1]
        assert parsed_data['reminder_minutes'] is None


# ==================== Tests for update_note Action ====================

class TestUpdateNoteAction:
    """Test update_note action handling in /api/message endpoint."""

    @patch('app.update_event_note')
    @patch('app.groq_client')
    def test_update_note_action_handled(self, mock_groq, mock_update_event_note, client, mock_auth):
        """Test update_note action is handled correctly."""
        # Mock Groq response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "action": "update_note",
            "title": "meeting",
            "date": "2026-03-01",
            "time": None,
            "end_time": None,
            "new_date": None,
            "new_time": None,
            "new_end_time": None,
            "note": "call John first",
            "reminder_minutes": None,
            "confidence": 0.85
        })
        mock_groq.chat.completions.create.return_value = mock_response

        # Mock update_event_note success response
        mock_update_event_note.return_value = {
            'success': True,
            'message': 'Note added to "Meeting"',
            'event': {
                'id': 'event123',
                'title': 'Meeting',
                'start': '2026-03-01T15:00:00',
                'end': '2026-03-01T16:00:00'
            },
            'needs_confirmation': False
        }

        # Send request
        response = client.post('/api/message', json={
                'message': 'add a note to my meeting tomorrow: call John first'
            })

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'call John first' in data['message']

        # Verify update_event_note was called
        mock_update_event_note.assert_called_once()
        call_args = mock_update_event_note.call_args[0]
        assert call_args[0] == 'user123'  # user_id
        assert call_args[2] == 'call John first'  # note

    @patch('app.update_event_note')
    @patch('app.groq_client')
    def test_update_note_with_update_keyword(self, mock_groq, mock_update_event_note, client, mock_auth):
        """Test update_note action with 'update' keyword."""
        # Mock Groq response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "action": "update_note",
            "title": "dentist appointment",
            "date": "2026-03-05",
            "time": None,
            "end_time": None,
            "new_date": None,
            "new_time": None,
            "new_end_time": None,
            "note": "bring insurance card",
            "reminder_minutes": None,
            "confidence": 0.85
        })
        mock_groq.chat.completions.create.return_value = mock_response

        # Mock update_event_note success response
        mock_update_event_note.return_value = {
            'success': True,
            'message': 'Note added to "Dentist Appointment"',
            'event': {
                'id': 'event456',
                'title': 'Dentist Appointment',
                'start': '2026-03-05T14:00:00',
                'end': '2026-03-05T15:00:00'
            },
            'needs_confirmation': False
        }

        # Send request
        response = client.post('/api/message', json={
                'message': 'update my dentist appointment Friday with note: bring insurance card'
            })

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'bring insurance card' in data['message']

        # Verify update_event_note was called
        mock_update_event_note.assert_called_once()
        call_args = mock_update_event_note.call_args[0]
        assert call_args[0] == 'user123'  # user_id
        assert call_args[2] == 'bring insurance card'  # note


# ==================== Tests for Conversational Responses ====================

class TestConversationalResponses:
    """Test conversational responses mention reminder times."""

    @patch('app.create_event')
    @patch('app.groq_client')
    def test_response_mentions_30min_reminder(self, mock_groq, mock_create_event, client, mock_auth):
        """Test response mentions '30 minutes' for default reminder."""
        # Mock Groq response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "action": "create",
            "title": "meeting",
            "date": "2026-03-01",
            "time": "15:00",
            "end_time": None,
            "new_date": None,
            "new_time": None,
            "new_end_time": None,
            "note": None,
            "confidence": 0.95
        })
        mock_groq.chat.completions.create.return_value = mock_response

        # Mock create_event success response with 30 minute reminder
        mock_create_event.return_value = {
            'success': True,
            'message': 'Event created',
            'event': {
                'id': 'event123',
                'title': 'Meeting',
                'start': '2026-03-01T15:00:00',
                'end': '2026-03-01T16:00:00',
                'reminder_minutes': 30
            }
        }

        # Send request
        response = client.post('/api/message', json={
                'message': 'schedule a meeting tomorrow at 3pm'
            })

        # Debug: Print response
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")

        # Verify response mentions reminder
        data = json.loads(response.data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {data}"
        assert '30 minute' in data['message']
        assert 'reminded' in data['message'].lower()

    @patch('app.create_event')
    @patch('app.groq_client')
    def test_response_mentions_1_hour_reminder(self, mock_groq, mock_create_event, client, mock_auth):
        """Test response mentions '1 hour' for 60 minute reminder."""
        # Mock Groq response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "action": "create",
            "title": "dentist appointment",
            "date": "2026-03-01",
            "time": "14:00",
            "end_time": None,
            "new_date": None,
            "new_time": None,
            "new_end_time": None,
            "note": None,
            "reminder_minutes": 60,
            "confidence": 0.90
        })
        mock_groq.chat.completions.create.return_value = mock_response

        # Mock create_event success response with 60 minute reminder
        mock_create_event.return_value = {
            'success': True,
            'message': 'Event created',
            'event': {
                'id': 'event123',
                'title': 'Dentist Appointment',
                'start': '2026-03-01T14:00:00',
                'end': '2026-03-01T15:00:00',
                'reminder_minutes': 60
            }
        }

        # Send request
        response = client.post('/api/message', json={
                'message': 'schedule dentist appointment tomorrow at 2pm, remind me 1 hour before'
            })

        # Debug: Print response
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")

        # Verify response mentions 1 hour
        data = json.loads(response.data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {data}"
        assert '1 hour' in data['message']
        assert 'reminded' in data['message'].lower()

    @patch('app.create_event')
    @patch('app.groq_client')
    def test_response_no_reminder_mention(self, mock_groq, mock_create_event, client, mock_auth):
        """Test response does NOT mention reminder when reminder_minutes is null."""
        # Mock Groq response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "action": "create",
            "title": "meeting",
            "date": "2026-03-05",
            "time": "16:00",
            "end_time": None,
            "new_date": None,
            "new_time": None,
            "new_end_time": None,
            "note": None,
            "reminder_minutes": None,
            "confidence": 0.90
        })
        mock_groq.chat.completions.create.return_value = mock_response

        # Mock create_event success response with no reminder
        mock_create_event.return_value = {
            'success': True,
            'message': 'Event created',
            'event': {
                'id': 'event123',
                'title': 'Meeting',
                'start': '2026-03-05T16:00:00',
                'end': '2026-03-05T17:00:00',
                'reminder_minutes': None
            }
        }

        # Send request
        response = client.post('/api/message', json={
                'message': 'schedule a meeting Friday at 4pm without a reminder'
            })

        # Debug: Print response
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")

        # Verify response does NOT mention reminder
        data = json.loads(response.data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {data}"
        assert 'reminded' not in data['message'].lower()
        assert 'reminder' not in data['message'].lower()
