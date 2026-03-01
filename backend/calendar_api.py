"""
Google Calendar API Integration Module

Handles all interactions with the Google Calendar API including:
- Creating, deleting, moving, and listing events
- Date/time parsing and timezone handling
- Event searching with multiple match handling

IMPORTANT: All date/time operations use the user's local timezone,
not UTC, to ensure events appear at the correct times for the user.
"""

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
import re
import pytz
from database import get_refresh_token
from auth import refresh_access_token

# ==================== Timezone Cache ====================

# Cache user timezones to avoid repeated API calls
# Key: user_id, Value: timezone string (e.g., "America/Los_Angeles")
_timezone_cache = {}

# ==================== Calendar Service ====================

def get_calendar_service(user_id: str):
    """
    Create an authenticated Google Calendar API service for a user.

    This function:
    1. Retrieves the user's refresh token from database
    2. Gets a valid access token (refreshing if needed)
    3. Creates credentials object
    4. Builds and returns Calendar API service

    Args:
        user_id: UUID of the user

    Returns:
        googleapiclient.discovery.Resource: Authenticated Calendar API service

    Raises:
        Exception: If refresh token not found or token refresh fails
    """
    # Get the user's refresh token from database
    refresh_token = get_refresh_token(user_id)

    if not refresh_token:
        raise Exception("No refresh token found. Please log in again.")

    # Get a fresh access token using the refresh token
    access_token = refresh_access_token(refresh_token)

    # Create credentials object with the access token
    credentials = Credentials(token=access_token)

    # Build and return the Calendar API service
    # 'calendar' is the API name, 'v3' is the version
    service = build('calendar', 'v3', credentials=credentials)

    return service


def get_user_timezone(user_id: str, service=None):
    """
    Get the user's timezone from Google Calendar settings.

    Fetches the timezone once and caches it to avoid repeated API calls.
    The timezone is retrieved from the user's Google Calendar settings
    using service.settings().get(setting='timezone').execute()

    Args:
        user_id: UUID of the user
        service: Authenticated Calendar API service (optional)
                If not provided, will create one

    Returns:
        str: Timezone string (e.g., "America/Los_Angeles", "Europe/London")

    Example:
        get_user_timezone(user_id)
        Returns: "America/Los_Angeles"
    """
    # Check cache first - avoid API call if we already fetched it
    if user_id in _timezone_cache:
        return _timezone_cache[user_id]

    # Create service if not provided
    if service is None:
        service = get_calendar_service(user_id)

    try:
        # Fetch timezone setting from Google Calendar
        timezone_setting = service.settings().get(setting='timezone').execute()
        timezone = timezone_setting['value']

        # Cache it for future use
        _timezone_cache[user_id] = timezone

        return timezone
    except Exception as e:
        # If we can't get the timezone, fall back to America/Los_Angeles
        print(f"Error fetching user timezone: {str(e)}")
        print("Falling back to America/Los_Angeles")
        return 'America/Los_Angeles'


# ==================== Date/Time Parsing ====================

def parse_date_time(date_str: str, time_str: str = None):
    """
    Convert natural language dates/times to ISO format datetime strings.

    Handles relative dates like:
    - "today", "tomorrow", "yesterday"
    - Day names: "Monday", "Friday", etc.
    - Absolute dates: "2026-03-15", "March 15"

    Handles times like:
    - "3pm", "3:30pm", "15:00", "3:30"
    - Defaults to 12:00pm if no time provided

    Args:
        date_str: Date in natural language or ISO format
        time_str: Time in various formats (optional, defaults to 12:00pm)

    Returns:
        tuple: (start_datetime_str, end_datetime_str) in ISO format
               Event duration is 1 hour by default

    Example:
        parse_date_time("tomorrow", "3pm")
        Returns: ("2026-02-28T15:00:00", "2026-02-28T16:00:00")
    """
    # Get current date as starting point
    now = datetime.now()

    # Parse the date component
    date_lower = date_str.lower().strip()

    if date_lower == "today":
        event_date = now
    elif date_lower == "tomorrow":
        event_date = now + timedelta(days=1)
    elif date_lower == "yesterday":
        event_date = now - timedelta(days=1)
    elif date_lower in ["monday", "mon"]:
        event_date = now + timedelta(days=(0 - now.weekday()) % 7)
    elif date_lower in ["tuesday", "tue"]:
        event_date = now + timedelta(days=(1 - now.weekday()) % 7)
    elif date_lower in ["wednesday", "wed"]:
        event_date = now + timedelta(days=(2 - now.weekday()) % 7)
    elif date_lower in ["thursday", "thu"]:
        event_date = now + timedelta(days=(3 - now.weekday()) % 7)
    elif date_lower in ["friday", "fri"]:
        event_date = now + timedelta(days=(4 - now.weekday()) % 7)
    elif date_lower in ["saturday", "sat"]:
        event_date = now + timedelta(days=(5 - now.weekday()) % 7)
    elif date_lower in ["sunday", "sun"]:
        event_date = now + timedelta(days=(6 - now.weekday()) % 7)
    else:
        # Try to parse as absolute date using dateutil
        try:
            event_date = date_parser.parse(date_str)
        except:
            # If parsing fails, default to today
            event_date = now

    # Parse the time component
    if time_str:
        time_lower = time_str.lower().strip()

        # Handle various time formats: "3pm", "3:30pm", "15:00", etc.
        # Use regex to extract hour and minute
        time_match = re.match(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', time_lower)

        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            am_pm = time_match.group(3)

            # Convert to 24-hour format if am/pm specified
            if am_pm == 'pm' and hour != 12:
                hour += 12
            elif am_pm == 'am' and hour == 12:
                hour = 0

            # Combine date and time
            start_datetime = event_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        else:
            # Default to 12:00pm if time parsing fails
            start_datetime = event_date.replace(hour=12, minute=0, second=0, microsecond=0)
    else:
        # No time specified, default to 12:00pm
        start_datetime = event_date.replace(hour=12, minute=0, second=0, microsecond=0)

    # Event duration is 1 hour by default
    end_datetime = start_datetime + timedelta(hours=1)

    # Return in ISO format (YYYY-MM-DDTHH:MM:SS)
    # We don't include timezone suffix - Calendar API will use user's default calendar timezone
    return (
        start_datetime.strftime('%Y-%m-%dT%H:%M:%S'),
        end_datetime.strftime('%Y-%m-%dT%H:%M:%S')
    )


# ==================== Helper Functions ====================

def format_time_range(start_datetime_str: str, end_datetime_str: str):
    """
    Format event start and end times as a nice readable time range.

    Converts ISO 8601 format to readable format like "12:00 PM - 1:00 PM"
    Handles all-day events by returning "All day"

    Args:
        start_datetime_str: Start datetime in ISO format (e.g., "2026-03-04T12:00:00-08:00")
        end_datetime_str: End datetime in ISO format

    Returns:
        str: Formatted time range (e.g., "12:00 PM - 1:00 PM") or "All day"

    Example:
        format_time_range("2026-03-04T12:00:00-08:00", "2026-03-04T13:00:00-08:00")
        Returns: "12:00 PM - 1:00 PM"
    """
    try:
        # Check if it's an all-day event (date only, no time component)
        if 'T' not in start_datetime_str:
            return "All day"

        # Parse the ISO datetime strings
        start_dt = datetime.fromisoformat(start_datetime_str.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_datetime_str.replace('Z', '+00:00'))

        # Format times as "12:00 PM" style
        # Try %-I first (works on macOS/Linux), fallback to %I (cross-platform)
        try:
            start_time = start_dt.strftime('%-I:%M %p')
            end_time = end_dt.strftime('%-I:%M %p')
        except ValueError:
            # Fallback for Windows - use %I and manually remove leading zero from hour only
            start_formatted = start_dt.strftime('%I:%M %p')
            end_formatted = end_dt.strftime('%I:%M %p')
            # Remove leading zero only if it's at the start (e.g., "03" -> "3", but not "10")
            start_time = start_formatted[1:] if start_formatted[0] == '0' else start_formatted
            end_time = end_formatted[1:] if end_formatted[0] == '0' else end_formatted

        return f"{start_time} - {end_time}"
    except:
        # If parsing fails, return the original strings
        return f"{start_datetime_str} - {end_datetime_str}"


# ==================== Event Search ====================

def search_events(user_id: str, service, title: str = None, date_str: str = None, time_str: str = None):
    """
    Search for events by title, date, and/or time.

    Used by delete and move operations to find matching events.
    Returns ALL matching events so user can confirm which one they mean.

    IMPORTANT: If time is specified, only returns events that start at that time.
    This prevents accidentally deleting/moving the wrong event when user specifies
    a time (e.g., "cancel my meeting at 6pm" won't match a 3pm meeting).

    Args:
        user_id: UUID of the user (for timezone lookup)
        service: Authenticated Calendar API service
        title: Event title to search for (case-insensitive, optional)
        date_str: Date to search on (optional)
        time_str: Time to search for (e.g., "3pm", "14:30") (optional)

    Returns:
        list: List of matching events, each with:
              - id: Event ID
              - title: Event summary
              - start: Start datetime
              - end: End datetime

    Example:
        search_events(user_id, service, "meeting", "tomorrow", "3pm")
        Returns only events with "meeting" in the title that start at 3pm tomorrow
    """
    # Get user's timezone to build correct date range
    user_timezone = get_user_timezone(user_id, service)
    tz = pytz.timezone(user_timezone)

    # Determine time range to search
    if date_str:
        # Parse the date and search that entire day IN USER'S TIMEZONE
        start_dt, end_dt = parse_date_time(date_str)
        # Convert to datetime object (naive)
        start_dt_obj = datetime.fromisoformat(start_dt)

        # Create timezone-aware datetimes for start and end of day in user's timezone
        # This ensures we search the correct 24-hour period in their local time
        day_start = tz.localize(start_dt_obj.replace(hour=0, minute=0, second=0))
        day_end = tz.localize(start_dt_obj.replace(hour=23, minute=59, second=59))

        # Convert to RFC3339 format for Google Calendar API
        time_min = day_start.isoformat()
        time_max = day_end.isoformat()
    else:
        # Search next 30 days if no date specified
        now = datetime.now(tz)
        time_min = now.isoformat()
        time_max = (now + timedelta(days=30)).isoformat()

    # Fetch events from Google Calendar
    try:
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,  # Expand recurring events
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
    except Exception as e:
        print(f"Error fetching events: {str(e)}")
        return []

    # Parse target time if specified for filtering
    target_hour = None
    target_minute = None
    if time_str:
        # Parse the time to get hour and minute
        time_lower = time_str.lower().strip()
        time_match = re.match(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', time_lower)

        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            am_pm = time_match.group(3)

            # Convert to 24-hour format if am/pm specified
            if am_pm == 'pm' and hour != 12:
                hour += 12
            elif am_pm == 'am' and hour == 12:
                hour = 0

            target_hour = hour
            target_minute = minute

    # Filter events based on criteria
    matching_events = []

    for event in events:
        event_title = event.get('summary', '').lower()
        event_start = event['start'].get('dateTime', event['start'].get('date'))

        # Check title match if specified (using fuzzy/partial word matching)
        if title:
            title_lower = title.lower()
            # Split both search query and event title into words
            search_words = set(title_lower.split())
            event_words = set(event_title.split())

            # Check if any word from search query appears in event title, or vice versa
            # This handles cases like:
            # - "standup meeting" finds "Standup"
            # - "meeting" finds "Team Meeting"
            # - "dentist" finds "Dentist Appointment"
            match_found = False
            for search_word in search_words:
                for event_word in event_words:
                    # Check if either word contains the other (handles partial matches)
                    if search_word in event_word or event_word in search_word:
                        match_found = True
                        break
                if match_found:
                    break

            if not match_found:
                continue  # Skip this event, title doesn't match

        # Check time match if specified
        if target_hour is not None:
            # Parse event start time
            try:
                # Handle both datetime strings (with time) and date strings (all-day events)
                if 'T' in event_start:
                    event_dt = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
                    event_hour = event_dt.hour
                    event_minute = event_dt.minute

                    # Check if event starts at the specified time
                    # Match exact hour and minute
                    if event_hour != target_hour or event_minute != target_minute:
                        continue  # Skip this event, time doesn't match
                else:
                    # All-day event, can't match a specific time
                    continue  # Skip this event
            except:
                continue  # Skip if we can't parse the datetime

        # Event matches all specified criteria
        event_end = event['end'].get('dateTime', event['end'].get('date'))

        # Format the time range nicely (e.g., "12:00 PM - 1:00 PM")
        time_range = format_time_range(event_start, event_end)

        matching_events.append({
            'id': event['id'],
            'title': event.get('summary', 'Untitled'),
            'start': event_start,
            'end': event_end,
            'time': time_range  # Nicely formatted time
        })

    return matching_events


# ==================== Create Event ====================

def create_event(user_id: str, event_data: dict):
    """
    Create a new event on the user's Google Calendar.

    Args:
        user_id: UUID of the user
        event_data: Dictionary with:
                   - title: Event title/summary
                   - date: Date string (e.g., "tomorrow", "Friday", "2026-03-15")
                   - time: Time string (e.g., "3pm", "14:30") - optional
                   - end_time: End time string (e.g., "5pm", "17:00") - optional

    Returns:
        dict: Result with:
              - success: True/False
              - message: Success/error message
              - event: Created event details (if successful)

    Example:
        create_event(user_id, {
            "title": "Meeting with John",
            "date": "tomorrow",
            "time": "3pm",
            "end_time": "5pm"
        })
    """
    try:
        # Get authenticated Calendar API service
        service = get_calendar_service(user_id)

        # Get user's timezone from Google Calendar settings
        user_timezone = get_user_timezone(user_id, service)

        # Parse the date and time
        title = event_data.get('title', 'Untitled Event').title()
        date_str = event_data.get('date', 'today')
        time_str = event_data.get('time')
        end_time_str = event_data.get('end_time')

        # Get start and default end (start + 1 hour)
        start_datetime, default_end_datetime = parse_date_time(date_str, time_str)

        # If end_time was provided, parse it and combine with date
        if end_time_str:
            # Parse the end time with the same date
            # Take the first value (the actual end time), not the second (end time + 1 hour)
            custom_end_datetime, _ = parse_date_time(date_str, end_time_str)
            end_datetime = custom_end_datetime
        else:
            # Use default end time (start + 1 hour)
            end_datetime = default_end_datetime

        # Create event object for Google Calendar API
        event = {
            'summary': title,
            'start': {
                'dateTime': start_datetime,
                # Use user's calendar timezone
                # This ensures the event appears at the correct local time
                'timeZone': user_timezone,
            },
            'end': {
                'dateTime': end_datetime,
                'timeZone': user_timezone,
            },
        }

        # Insert the event into the user's primary calendar
        created_event = service.events().insert(calendarId='primary', body=event).execute()

        return {
            'success': True,
            'message': f'Event "{title}" created successfully',
            'event': {
                'id': created_event['id'],
                'title': created_event.get('summary'),
                'start': created_event['start'].get('dateTime'),
                'end': created_event['end'].get('dateTime'),
                'link': created_event.get('htmlLink')
            }
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Failed to create event: {str(e)}',
            'event': None
        }


# ==================== Delete Event ====================

def delete_event(user_id: str, event_query: dict):
    """
    Delete an event from the user's Google Calendar.

    IMPORTANT: If multiple events match, returns all matches for user confirmation
    instead of blindly deleting the first one.

    IMPORTANT: If a time is specified, only matches events at that exact time.
    This prevents accidentally deleting the wrong event (e.g., "cancel my meeting
    at 6pm" won't delete a 3pm meeting).

    Args:
        user_id: UUID of the user
        event_query: Dictionary with:
                    - title: Event title to search for (optional)
                    - date: Date to search on (optional)
                    - time: Time to match (e.g., "3pm", "14:30") (optional)
                    - event_id: Specific event ID (optional, for confirmation)

    Returns:
        dict: Result with:
              - success: True/False
              - message: Success/error message
              - multiple_matches: List of matching events (if multiple found)
              - needs_confirmation: True if user needs to choose from multiple

    Example:
        delete_event(user_id, {"title": "meeting", "date": "Friday", "time": "3pm"})
    """
    try:
        # Get authenticated Calendar API service
        service = get_calendar_service(user_id)

        # Check if user is confirming a specific event ID
        if 'event_id' in event_query:
            # User has confirmed which event to delete
            event_id = event_query['event_id']

            try:
                service.events().delete(calendarId='primary', eventId=event_id).execute()
                return {
                    'success': True,
                    'message': 'Event deleted successfully',
                    'needs_confirmation': False
                }
            except Exception as e:
                return {
                    'success': False,
                    'message': f'Failed to delete event: {str(e)}',
                    'needs_confirmation': False
                }

        # Search for matching events
        title = event_query.get('title')
        date_str = event_query.get('date')
        time_str = event_query.get('time')

        matching_events = search_events(user_id, service, title, date_str, time_str)

        if len(matching_events) == 0:
            # Provide helpful error message if time was specified
            if time_str:
                return {
                    'success': False,
                    'message': f'No events found at {time_str}' + (f' on {date_str}' if date_str else ''),
                    'needs_confirmation': False
                }
            else:
                return {
                    'success': False,
                    'message': 'No matching events found',
                    'needs_confirmation': False
                }
        elif len(matching_events) == 1:
            # Only one match - safe to delete
            event_id = matching_events[0]['id']
            service.events().delete(calendarId='primary', eventId=event_id).execute()

            return {
                'success': True,
                'message': f'Event "{matching_events[0]["title"]}" deleted successfully',
                'needs_confirmation': False
            }
        else:
            # Multiple matches - ask user to confirm which one
            return {
                'success': False,
                'message': f'Found {len(matching_events)} matching events. Please specify which one:',
                'multiple_matches': matching_events,
                'needs_confirmation': True
            }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error searching for events: {str(e)}',
            'needs_confirmation': False
        }


# ==================== Move Event ====================

def move_event(user_id: str, event_query: dict, new_date: str, new_time: str = None, new_end_time: str = None):
    """
    Move/reschedule an event to a new date and time.

    IMPORTANT: If multiple events match, returns all matches for user confirmation
    instead of blindly moving the first one.

    IMPORTANT: If a time is specified in event_query, only matches events at that
    exact time. This prevents accidentally moving the wrong event (e.g., "move my
    meeting at 6pm" won't move a 3pm meeting).

    Args:
        user_id: UUID of the user
        event_query: Dictionary with:
                    - title: Event title to search for (optional)
                    - date: Current date to search on (optional)
                    - time: Current time to match (e.g., "3pm", "14:30") (optional)
                    - event_id: Specific event ID (optional, for confirmation)
        new_date: New date for the event
        new_time: New time for the event (optional)
        new_end_time: New end time for the event (optional)

    Returns:
        dict: Result with:
              - success: True/False
              - message: Success/error message
              - event: Updated event details (if successful)
              - multiple_matches: List of matching events (if multiple found)
              - needs_confirmation: True if user needs to choose from multiple

    Example:
        move_event(user_id, {"title": "meeting", "time": "3pm"}, "Thursday", "4pm", "6pm")
    """
    try:
        # Get authenticated Calendar API service
        service = get_calendar_service(user_id)

        # Get user's timezone from Google Calendar settings
        user_timezone = get_user_timezone(user_id, service)

        # Check if user is confirming a specific event ID
        if 'event_id' in event_query:
            # User has confirmed which event to move
            event_id = event_query['event_id']

            try:
                # Get the event
                event = service.events().get(calendarId='primary', eventId=event_id).execute()

                # Parse new date and time
                new_start, default_new_end = parse_date_time(new_date, new_time)

                # If new_end_time was provided, parse it and combine with new_date
                if new_end_time:
                    # Take the first value (the actual end time), not the second (end time + 1 hour)
                    custom_new_end, _ = parse_date_time(new_date, new_end_time)
                    new_end = custom_new_end
                else:
                    # Use default end time (start + 1 hour) or preserve original duration
                    # Calculate original duration
                    original_start = event['start'].get('dateTime')
                    original_end = event['end'].get('dateTime')

                    if original_start and original_end:
                        # Preserve original duration when moving
                        original_start_dt = datetime.fromisoformat(original_start.replace('Z', '+00:00'))
                        original_end_dt = datetime.fromisoformat(original_end.replace('Z', '+00:00'))
                        duration = original_end_dt - original_start_dt

                        # Apply same duration to new start time
                        new_start_dt = datetime.fromisoformat(new_start)
                        new_end_dt = new_start_dt + duration
                        new_end = new_end_dt.strftime('%Y-%m-%dT%H:%M:%S')
                    else:
                        # Fall back to default (start + 1 hour)
                        new_end = default_new_end

                # Update event times
                event['start'] = {
                    'dateTime': new_start,
                    'timeZone': user_timezone,
                }
                event['end'] = {
                    'dateTime': new_end,
                    'timeZone': user_timezone,
                }

                # Update the event
                updated_event = service.events().update(
                    calendarId='primary',
                    eventId=event_id,
                    body=event
                ).execute()

                return {
                    'success': True,
                    'message': f'Event moved to {new_date}' + (f' at {new_time}' if new_time else ''),
                    'event': {
                        'id': updated_event['id'],
                        'title': updated_event.get('summary'),
                        'start': updated_event['start'].get('dateTime'),
                        'end': updated_event['end'].get('dateTime')
                    },
                    'needs_confirmation': False
                }
            except Exception as e:
                return {
                    'success': False,
                    'message': f'Failed to move event: {str(e)}',
                    'needs_confirmation': False
                }

        # Search for matching events
        title = event_query.get('title')
        date_str = event_query.get('date')
        time_str = event_query.get('time')

        matching_events = search_events(user_id, service, title, date_str, time_str)

        if len(matching_events) == 0:
            # Provide helpful error message if time was specified
            if time_str:
                return {
                    'success': False,
                    'message': f'No events found at {time_str}' + (f' on {date_str}' if date_str else ''),
                    'needs_confirmation': False
                }
            else:
                return {
                    'success': False,
                    'message': 'No matching events found',
                    'needs_confirmation': False
                }
        elif len(matching_events) == 1:
            # Only one match - safe to move
            event_id = matching_events[0]['id']

            # Get the event
            event = service.events().get(calendarId='primary', eventId=event_id).execute()

            # Parse new date and time
            new_start, default_new_end = parse_date_time(new_date, new_time)

            # If new_end_time was provided, parse it and combine with new_date
            if new_end_time:
                # Take the first value (the actual end time), not the second (end time + 1 hour)
                custom_new_end, _ = parse_date_time(new_date, new_end_time)
                new_end = custom_new_end
            else:
                # Use default end time (start + 1 hour) or preserve original duration
                # Calculate original duration
                original_start = event['start'].get('dateTime')
                original_end = event['end'].get('dateTime')

                if original_start and original_end:
                    # Preserve original duration when moving
                    original_start_dt = datetime.fromisoformat(original_start.replace('Z', '+00:00'))
                    original_end_dt = datetime.fromisoformat(original_end.replace('Z', '+00:00'))
                    duration = original_end_dt - original_start_dt

                    # Apply same duration to new start time
                    new_start_dt = datetime.fromisoformat(new_start)
                    new_end_dt = new_start_dt + duration
                    new_end = new_end_dt.strftime('%Y-%m-%dT%H:%M:%S')
                else:
                    # Fall back to default (start + 1 hour)
                    new_end = default_new_end

            # Update event times
            event['start'] = {
                'dateTime': new_start,
                'timeZone': user_timezone,
            }
            event['end'] = {
                'dateTime': new_end,
                'timeZone': user_timezone,
            }

            # Update the event
            updated_event = service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()

            return {
                'success': True,
                'message': f'Event "{updated_event.get("summary")}" moved successfully',
                'event': {
                    'id': updated_event['id'],
                    'title': updated_event.get('summary'),
                    'start': updated_event['start'].get('dateTime'),
                    'end': updated_event['end'].get('dateTime')
                },
                'needs_confirmation': False
            }
        else:
            # Multiple matches - ask user to confirm which one
            return {
                'success': False,
                'message': f'Found {len(matching_events)} matching events. Please specify which one:',
                'multiple_matches': matching_events,
                'needs_confirmation': True
            }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error searching for events: {str(e)}',
            'needs_confirmation': False
        }


# ==================== List Events ====================

def list_events(user_id: str, date_query: str = None, time_query: str = None):
    """
    List events for a specific date or date range.

    If time is specified, only returns events at that exact time.
    This allows queries like "What do I have at 3pm tomorrow?"

    Args:
        user_id: UUID of the user
        date_query: Date to list events for (e.g., "today", "Friday", "tomorrow")
                   If None, lists next 7 days
        time_query: Time to filter for (e.g., "3pm", "14:30") (optional)

    Returns:
        dict: Result with:
              - success: True/False
              - message: Success/error message
              - events: List of events with details

    Example:
        list_events(user_id, "Friday", "3pm")
    """
    try:
        # Get authenticated Calendar API service
        service = get_calendar_service(user_id)

        # Get user's timezone to build correct date range
        user_timezone = get_user_timezone(user_id, service)
        tz = pytz.timezone(user_timezone)

        # Determine time range
        if date_query:
            # List events for specific day IN USER'S TIMEZONE
            start_dt, _ = parse_date_time(date_query)
            start_dt_obj = datetime.fromisoformat(start_dt)

            # Create timezone-aware datetimes for start and end of day in user's timezone
            day_start = tz.localize(start_dt_obj.replace(hour=0, minute=0, second=0))
            day_end = tz.localize(start_dt_obj.replace(hour=23, minute=59, second=59))

            # Convert to RFC3339 format for Google Calendar API
            time_min = day_start.isoformat()
            time_max = day_end.isoformat()
        else:
            # List next 7 days
            now = datetime.now(tz)
            time_min = now.isoformat()
            time_max = (now + timedelta(days=7)).isoformat()

        # Fetch events
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        # Parse target time if specified for filtering
        target_hour = None
        target_minute = None
        if time_query:
            # Parse the time to get hour and minute
            time_lower = time_query.lower().strip()
            time_match = re.match(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', time_lower)

            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2) or 0)
                am_pm = time_match.group(3)

                # Convert to 24-hour format if am/pm specified
                if am_pm == 'pm' and hour != 12:
                    hour += 12
                elif am_pm == 'am' and hour == 12:
                    hour = 0

                target_hour = hour
                target_minute = minute

        # Format events for response, with optional time filtering
        formatted_events = []
        for event in events:
            event_start = event['start'].get('dateTime', event['start'].get('date'))

            # Filter by time if specified
            if target_hour is not None:
                # Parse event start time
                try:
                    # Handle both datetime strings (with time) and date strings (all-day events)
                    if 'T' in event_start:
                        event_dt = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
                        event_hour = event_dt.hour
                        event_minute = event_dt.minute

                        # Check if event starts at the specified time
                        if event_hour != target_hour or event_minute != target_minute:
                            continue  # Skip this event, time doesn't match
                    else:
                        # All-day event, can't match a specific time
                        continue  # Skip this event
                except:
                    continue  # Skip if we can't parse the datetime

            event_end = event['end'].get('dateTime', event['end'].get('date'))

            # Format the time range nicely (e.g., "12:00 PM - 1:00 PM")
            time_range = format_time_range(event_start, event_end)

            formatted_events.append({
                'id': event['id'],
                'title': event.get('summary', 'Untitled'),
                'start': event_start,
                'end': event_end,
                'time': time_range,  # Nicely formatted time
                'location': event.get('location', '')
            })

        if not formatted_events:
            if time_query:
                return {
                    'success': True,
                    'message': f'No events found at {time_query}' + (f' on {date_query}' if date_query else ''),
                    'events': []
                }
            else:
                return {
                    'success': True,
                    'message': f'No events found for {date_query or "the next 7 days"}',
                    'events': []
                }

        return {
            'success': True,
            'message': f'Found {len(formatted_events)} event(s)',
            'events': formatted_events
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error fetching events: {str(e)}',
            'events': []
        }


# ==================== Get All Events (for Calendar View) ====================

def get_all_events(user_id: str, time_min: str, time_max: str):
    """
    Get all events in a date range for calendar display.

    Used by the frontend calendar component to populate the view.

    Args:
        user_id: UUID of the user
        time_min: Start date (ISO format or 'Z' suffix for UTC)
        time_max: End date (ISO format or 'Z' suffix for UTC)

    Returns:
        list: List of events with:
              - id: Event ID
              - title: Event summary
              - start: Start datetime
              - end: End datetime
              - allDay: Boolean indicating all-day event

    Example:
        get_all_events(user_id, "2026-03-01T00:00:00Z", "2026-03-31T23:59:59Z")
    """
    try:
        # Get authenticated Calendar API service
        service = get_calendar_service(user_id)

        # Fetch events from Google Calendar
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,  # Expand recurring events
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        # Format events for frontend calendar component
        formatted_events = []
        for event in events:
            # Check if it's an all-day event (has 'date' instead of 'dateTime')
            is_all_day = 'date' in event['start']

            formatted_events.append({
                'id': event['id'],
                'title': event.get('summary', 'Untitled'),
                'start': event['start'].get('dateTime') or event['start'].get('date'),
                'end': event['end'].get('dateTime') or event['end'].get('date'),
                'allDay': is_all_day
            })

        return formatted_events

    except Exception as e:
        print(f"Error fetching events for calendar: {str(e)}")
        return []
