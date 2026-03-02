"""
JustScheduleIt Flask API Server

Main application file that defines all API endpoints.

Features:
- Google OAuth 2.0 authentication
- JWT session management with httpOnly cookies
- Natural language command parsing with Groq API (Llama 3.1)
- Protected endpoints requiring authentication

Endpoints:
- /api/auth/login - Initiate Google OAuth flow
- /api/auth/callback - Handle OAuth callback and issue JWT
- /api/auth/user - Get current user info (protected)
- /api/auth/logout - Logout user (protected)
- /api/message - Parse and execute calendar commands with AI (protected)
- /api/calendar/events - Fetch calendar events for date range (protected)
- /api/health - Health check
"""

from flask import Flask, request, jsonify, g, make_response, redirect, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
from groq import Groq
import json
from datetime import datetime, timedelta
import re

# Import authentication functions
# These handle Google OAuth flow and JWT session management
from auth import (
    get_google_auth_url,         # Generate OAuth URL to redirect user to Google
    exchange_code_for_tokens,    # Exchange OAuth code for access/refresh tokens
    get_google_user_info,        # Get user profile from Google
    create_jwt,                  # Create JWT for session management
    require_auth,                # Decorator to protect routes
    refresh_access_token         # Get fresh access token from refresh token
)

# Import database functions
# These handle user and token storage in Supabase
from database import (
    get_user_by_google_id,  # Find user by their Google ID
    get_user_by_id,         # Find user by our internal UUID
    create_user,            # Create new user record
    store_refresh_token,    # Store encrypted refresh token
    get_refresh_token       # Retrieve encrypted refresh token for API calls
)

# Import Google Calendar API functions
# These handle calendar operations: create, delete, move, and list events
from calendar_api import (
    create_event,    # Create new calendar event
    delete_event,    # Delete calendar event (with multiple match handling)
    move_event,      # Move/reschedule calendar event (with multiple match handling)
    list_events,     # List events for specific date
    get_all_events,  # Get all events in a date range (for calendar view)
    parse_date_time  # Parse natural language dates to ISO format
)

# Initialize Flask application
app = Flask(__name__)

# Load configuration from Config class (which loads from .env)
app.config.from_object(Config)

# Set secret key for Flask session management (used for pending action confirmations)
# Use the JWT secret since both require secure random keys
app.secret_key = Config.JWT_SECRET

# Enable CORS (Cross-Origin Resource Sharing) for frontend requests
# origins: Which domains can make requests to this API
# supports_credentials=True: Required to send/receive httpOnly cookies
# Without this, the browser won't send cookies in cross-origin requests
CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)

# Initialize Groq AI client for natural language processing
# Used to parse calendar commands like "schedule meeting tomorrow at 3pm"
groq_client = Groq(api_key=Config.GROQ_API_KEY)


# ==================== Rate Limiting Setup ====================

def get_rate_limit_key():
    """
    Custom key function for rate limiting.

    For authenticated endpoints: Rate limit by user_id (extracted from JWT)
    For unauthenticated endpoints: Rate limit by IP address

    This prevents users from bypassing rate limits by logging out,
    while still protecting unauthenticated endpoints from abuse.
    """
    # Check if user is authenticated (user_id set by @require_auth decorator)
    if hasattr(g, 'user_id') and g.user_id:
        # Rate limit by user_id for authenticated requests
        return f"user:{g.user_id}"
    else:
        # Rate limit by IP address for unauthenticated requests
        return f"ip:{get_remote_address()}"


# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_rate_limit_key,
    default_limits=[]  # No default limits, we'll set per-endpoint
)


@app.errorhandler(429)
def ratelimit_handler(e):
    """
    Custom error handler for rate limit exceeded (429 status).

    Returns a friendly error message instead of the default Flask-Limiter message.
    """
    return jsonify({
        'success': False,
        'error': "You're sending too many requests. Please wait a moment and try again."
    }), 429


# ==================== Helper Functions for Conversational Responses ====================

def format_date_conversational(date_str):
    """
    Format a date string conversationally.

    Converts "2026-03-01", "tomorrow", or "friday" to "March 1st, 2026"

    Args:
        date_str: Date string in ISO format or natural language

    Returns:
        str: Formatted date like "March 1st, 2026"
    """
    try:
        # If it's already a datetime object
        if isinstance(date_str, datetime):
            dt = date_str
        # If it's an ISO datetime string with T
        elif 'T' in str(date_str):
            dt = datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
        else:
            # Try to parse as ISO date first
            try:
                dt = datetime.fromisoformat(str(date_str))
            except:
                # If that fails, it might be natural language like "tomorrow", "friday"
                # Use parse_date_time to convert it to ISO format
                parsed_start, _ = parse_date_time(str(date_str))
                dt = datetime.fromisoformat(parsed_start)

        # Get the day with ordinal suffix (1st, 2nd, 3rd, etc.)
        day = dt.day
        if 10 <= day % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

        # Format as "March 1st, 2026"
        return dt.strftime(f'%B {day}{suffix}, %Y')
    except:
        return str(date_str)


def format_time_conversational(time_str):
    """
    Format a time string conversationally.

    Converts "15:00", "3pm", or ISO datetime to "3:00 PM"

    Args:
        time_str: Time string in various formats

    Returns:
        str: Formatted time like "3:00 PM"
    """
    try:
        # If it's a full ISO datetime string
        if 'T' in str(time_str):
            dt = datetime.fromisoformat(str(time_str).replace('Z', '+00:00'))
        else:
            # Check if it's already in conversational format (e.g., "3pm", "3:30pm")
            time_lower = str(time_str).lower().strip()
            if 'am' in time_lower or 'pm' in time_lower:
                # Parse formats like "3pm", "3:30pm", "3 pm", "3:30 pm"
                time_match = re.match(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', time_lower)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2) or 0)
                    am_pm = time_match.group(3).upper()

                    # Return formatted string
                    return f"{hour}:{minute:02d} {am_pm}"

            # Try parsing as HH:MM format
            dt = datetime.strptime(str(time_str), '%H:%M')

        # Format as "3:00 PM" (remove leading zero from hour)
        try:
            return dt.strftime('%-I:%M %p')
        except ValueError:
            # Fallback for Windows
            formatted = dt.strftime('%I:%M %p')
            return formatted[1:] if formatted[0] == '0' else formatted
    except:
        return str(time_str)


def generate_conversational_response(action, parsed_data, result):
    """
    Generate a friendly, conversational response based on the action and result.

    Removes technical data and creates natural language responses.

    Args:
        action: The action type (create, delete, move, list)
        parsed_data: The parsed command data
        result: The execution result

    Returns:
        str: Friendly conversational message
    """
    # Handle errors
    if not result.get('success', False):
        message = result.get('message', 'Something went wrong')

        # Check for multiple matches
        if result.get('needs_confirmation') and result.get('multiple_matches'):
            matches = result['multiple_matches']
            response = "I found multiple matches - which one did you mean?\n\n"

            for i, match in enumerate(matches, 1):
                title = match.get('title', 'Untitled')
                time_range = match.get('time', '')

                if time_range:
                    response += f"{i}. {title} ({time_range})\n"
                else:
                    # Parse the start time if time field not available
                    start = match.get('start', '')
                    if 'T' in start:
                        time = format_time_conversational(start)
                        response += f"{i}. {title} at {time}\n"
                    else:
                        response += f"{i}. {title}\n"

            response += "\nType 1, 2, 3... to select, or type a new command to cancel."
            return response.strip()

        # Custom error message for no events found
        if 'No events found' in message or 'No matching events found' in message:
            time_str = parsed_data.get('time')
            date_str = parsed_data.get('date')
            title = parsed_data.get('title')

            if time_str and date_str:
                date_formatted = format_date_conversational(date_str)
                time_formatted = format_time_conversational(time_str)

                if title:
                    return f"Sorry, I couldn't find '{title}' at {time_formatted} on {date_formatted}"
                else:
                    return f"You have nothing scheduled at {time_formatted} on {date_formatted}"
            elif date_str:
                date_formatted = format_date_conversational(date_str)
                if title:
                    return f"Sorry, I couldn't find '{title}' on {date_formatted}"
                else:
                    return f"You have nothing scheduled for {date_formatted}"
            else:
                return f"Sorry, I couldn't find any matching events"

        # Generic error
        return f"Sorry, {message}"

    # Handle successful actions
    if action == 'create':
        # Get event info from result if available, otherwise use parsed data
        event_info = result.get('event') or {}
        title = event_info.get('title') or parsed_data.get('title', 'Event')

        # Use the actual start time from the created event if available
        start_time = event_info.get('start')
        if start_time:
            date_formatted = format_date_conversational(start_time)
            time_formatted = format_time_conversational(start_time)
        else:
            # Fallback to parsed data
            date_str = parsed_data.get('date')
            time_str = parsed_data.get('time')
            date_formatted = format_date_conversational(date_str) if date_str else 'today'
            time_formatted = format_time_conversational(time_str) if time_str else '12:00 PM'

        return f"✓ Done! '{title}' scheduled for {date_formatted} at {time_formatted}"

    elif action == 'delete':
        # Get the title from result or parsed_data
        event_info = result.get('event') or {}
        title = event_info.get('title') or parsed_data.get('title', 'Event')
        date_str = parsed_data.get('date')

        date_formatted = format_date_conversational(date_str) if date_str else ''

        if date_formatted:
            return f"✓ Done! '{title}' on {date_formatted} has been cancelled"
        else:
            return f"✓ Done! '{title}' has been cancelled"

    elif action == 'move':
        # Get the title from result or parsed_data
        event_info = result.get('event') or {}
        title = event_info.get('title') or parsed_data.get('title', 'Event')
        new_date = parsed_data.get('new_date')
        new_time = parsed_data.get('new_time')

        date_formatted = format_date_conversational(new_date) if new_date else ''
        time_formatted = format_time_conversational(new_time) if new_time else ''

        if date_formatted and time_formatted:
            return f"✓ Done! '{title}' moved to {date_formatted} at {time_formatted}"
        elif date_formatted:
            return f"✓ Done! '{title}' moved to {date_formatted}"
        else:
            return f"✓ Done! '{title}' has been rescheduled"

    elif action == 'list':
        events = result.get('events', [])
        date_str = parsed_data.get('date')

        if not events:
            date_formatted = format_date_conversational(date_str) if date_str else 'that time'
            return f"You have nothing scheduled for {date_formatted}"

        # Format the header
        date_formatted = format_date_conversational(date_str) if date_str else 'your schedule'
        response = f"Here's what you have on {date_formatted}:\n\n"

        # Add each event
        for event in events:
            title = event.get('title', 'Untitled')
            time_range = event.get('time', '')

            if time_range:
                # Use the nicely formatted time range from backend
                response += f"• {time_range} - {title}\n"
            else:
                # Fallback: parse start time if time field not available
                start = event.get('start', '')
                if 'T' in start:
                    time = format_time_conversational(start)
                    response += f"• {time} - {title}\n"
                else:
                    # All-day event
                    response += f"• {title}\n"

        return response.strip()

    # Fallback
    return result.get('message', 'Done!')


# ==================== Authentication Endpoints ====================

@app.route('/api/auth/login', methods=['GET'])
@limiter.limit("10 per minute")
def login():
    """
    Initiate the Google OAuth 2.0 login flow.

    When a user wants to log in, they visit this endpoint in their browser.
    We redirect them to Google's consent screen where they:
    1. Choose their Google account
    2. Grant us permission to access their calendar
    3. Get redirected back to /api/auth/callback

    Returns:
        HTTP 302 redirect to Google's OAuth consent screen
    """
    try:
        # Generate the Google OAuth URL with our client ID and requested scopes
        auth_url = get_google_auth_url()

        # Redirect the user's browser to Google
        # Google will handle authentication and permission grants
        return redirect(auth_url)
    except Exception as e:
        # Log the error for debugging
        print(f"Error initiating login: {str(e)}")

        # Return error response (user won't see this often - redirect usually works)
        return jsonify({
            'success': False,
            'error': 'Failed to initiate login'
        }), 500


@app.route('/api/auth/callback', methods=['GET'])
def auth_callback():
    """
    Handle Google OAuth callback after user grants permissions.

    This is the MOST IMPORTANT endpoint in the auth flow. After the user grants
    permissions on Google's consent screen, Google redirects back here with an
    authorization code. We then:
    1. Exchange the code for tokens (access token + refresh token)
    2. Use the access token to get user's profile info
    3. Create/update the user in our database
    4. Store the encrypted refresh token
    5. Create a JWT for session management
    6. Set the JWT in an httpOnly cookie
    7. Redirect user to the frontend dashboard

    Returns:
        HTTP 302 redirect to frontend dashboard with JWT cookie set
    """
    try:
        # STEP 1: Extract the authorization code from the URL query parameters
        # Google adds this as: ?code=4/0Adeu5BW...
        code = request.args.get('code')

        if not code:
            # No code means something went wrong with Google's redirect
            return jsonify({
                'success': False,
                'error': 'No authorization code provided'
            }), 400

        # STEP 2: Exchange the authorization code for tokens
        # The code is single-use and expires in ~10 minutes
        # We get back:
        # - access_token: Valid for ~1 hour, used for immediate API calls
        # - refresh_token: Valid indefinitely, used to get new access tokens
        tokens = exchange_code_for_tokens(code)
        access_token = tokens['access_token']
        refresh_token = tokens['refresh_token']

        # STEP 3: Use the access token to fetch the user's Google profile
        # This gives us their ID, email, name, and profile picture
        user_info = get_google_user_info(access_token)

        # STEP 4: Check if this user already exists in our database
        # We use Google ID (not email) because it's permanent and never changes
        user = get_user_by_google_id(user_info['id'])
        if not user:
            # First time login - create a new user record
            user = create_user(
                google_id=user_info['id'],
                email=user_info['email'],
                name=user_info['name'],
                picture=user_info['picture']
            )

        # STEP 5: Store the refresh token (encrypted!) in the database
        # This allows us to make Calendar API calls later without re-prompting the user
        # The token is encrypted with Fernet before storage for security
        store_refresh_token(user['id'], refresh_token)

        # STEP 6: Create a JWT for session management
        # The JWT contains the user's database ID and expiration time
        # We'll use this JWT to identify the user on future requests
        jwt_token = create_jwt(user['id'])

        # STEP 7: Set the JWT in an httpOnly cookie and redirect to frontend
        # httpOnly=True: JavaScript can't access this cookie (prevents XSS attacks)
        # secure=False: For development (localhost uses HTTP not HTTPS)
        #               Set to True in production for security
        # samesite='Lax': Provides CSRF protection while allowing OAuth redirects
        # max_age: Cookie expires when JWT expires (1 hour by default)
        response = make_response(redirect('http://localhost:5173/dashboard'))
        response.set_cookie(
            'jwt_token',                    # Cookie name
            value=jwt_token,                # The actual JWT
            httponly=True,                  # Can't be accessed by JavaScript
            secure=False,                   # Set to True in production (HTTPS)
            samesite='Lax',                 # CSRF protection
            max_age=Config.JWT_EXPIRATION   # Expires with the JWT
        )

        # Redirect the user to the frontend dashboard
        # The cookie will be automatically included in future requests
        return response

    except Exception as e:
        # If anything goes wrong, log it and redirect to frontend with error
        print(f"Error in auth callback: {str(e)}")

        # Redirect to frontend homepage with error parameter
        # Frontend can check for ?error=auth_failed and show a message
        return redirect('http://localhost:5173?error=auth_failed')


@app.route('/api/auth/user', methods=['GET'])
@require_auth  # This decorator validates the JWT before the route runs
def get_current_user():
    """
    Get the current authenticated user's profile information.

    This is a protected route - the @require_auth decorator ensures the user
    has a valid JWT cookie before allowing access. Frontend can call this to:
    - Check if the user is logged in
    - Get the user's name and email to display in the UI
    - Fetch the profile picture

    The user_id is automatically extracted from the JWT by @require_auth
    and made available via Flask's g.user_id.

    Returns:
        JSON with user info (id, email, name, picture)
        or 401 if not authenticated
        or 404 if user not found in database
    """
    try:
        # Get the user_id that was extracted from the JWT by @require_auth
        # Flask's 'g' object is request-scoped global storage
        user_id = g.user_id

        # Fetch the full user record from the database
        user = get_user_by_id(user_id)

        if not user:
            # This shouldn't happen (JWT contains valid user_id)
            # but handle it just in case the user was deleted
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        # Return the user's profile information
        # Don't include sensitive fields like google_id or created_at
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],          # Our internal UUID
                'email': user['email'],    # User's email address
                'name': user['name'],      # Display name
                'picture': user['picture'] # Profile picture URL
            }
        }), 200

    except Exception as e:
        # Log any unexpected errors
        print(f"Error fetching user: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch user'
        }), 500


@app.route('/api/auth/logout', methods=['POST'])
@require_auth  # User must be logged in to log out (prevents errors)
def logout():
    """
    Logout the current user by deleting their JWT cookie.

    This invalidates the user's session. After logout, they'll need to go through
    the OAuth flow again to get a new JWT.

    Note: This only deletes the JWT cookie. The refresh token stays in our database
    (encrypted) so if the user logs in again, we don't need to re-prompt for
    calendar permissions. If you want to fully revoke access, you'd need to:
    1. Delete the refresh token from our database
    2. Revoke it with Google's API

    Returns:
        JSON success message with cookie deleted
    """
    try:
        # Create a success response
        response = make_response(jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }))

        # Delete the JWT cookie
        # This tells the browser to remove the jwt_token cookie
        # Future requests won't include the cookie, so @require_auth will fail
        response.delete_cookie('jwt_token')

        return response

    except Exception as e:
        # Log any unexpected errors
        print(f"Error during logout: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to logout'
        }), 500


# ==================== Message Endpoint ====================

@app.route('/api/message', methods=['POST'])
@require_auth  # Protected route - user must be logged in
@limiter.limit("30 per minute")
def handle_message():
    """
    Parse natural language calendar commands using Groq AI (Llama 3.1 8B Instant).

    This endpoint takes a user's natural language input like:
    - "schedule a meeting with John tomorrow at 3pm"
    - "cancel my dentist appointment Friday"
    - "move my 2pm meeting to Thursday at 4pm"

    And returns structured JSON that tells us:
    - What action to take (create/delete/move/list)
    - Event title
    - Date and time information
    - Confidence score

    Phase 3A: Authentication required (user must be logged in)
    Phase 3C: Will use the parsed data to actually modify Google Calendar

    Expected JSON payload:
    {
        "message": "user's natural language command"
    }

    Returns:
    {
        "success": true,
        "data": {
            "action": "create|delete|move|list",
            "title": "event name",
            "date": "YYYY-MM-DD",
            "time": "HH:MM or null",
            "end_time": "HH:MM or null",
            "new_date": "YYYY-MM-DD (move only) or null",
            "new_time": "HH:MM (move only) or null",
            "new_end_time": "HH:MM (move only) or null",
            "confidence": 0.0 to 1.0
        }
    }
    """
    try:
        # Get the authenticated user's ID from the JWT
        # This is set by @require_auth and stored in Flask's g object
        user_id = g.user_id

        # Parse the incoming JSON request body
        data = request.get_json()

        # Validate that the required 'message' field is present
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Message field is required'
            }), 400

        user_message = data['message'].strip()

        # Validate message length (max 500 characters)
        if len(user_message) > 500:
            return jsonify({
                'success': False,
                'error': 'Your message is too long. Please keep commands under 500 characters.'
            }), 400

        # ==================== CONFIRMATION FLOW ====================
        # Check if there's a pending action waiting for user confirmation
        # This happens when multiple events matched the previous command
        pending_action = session.get('pending_action')

        if pending_action:
            # User has a pending action - check if they're confirming a selection
            # Look for patterns like: "1", "2", "option 1", "the first one", etc.
            selection_match = re.match(r'^(?:option\s+)?(\d)(?:st|nd|rd|th)?$', user_message.lower())
            number_match = re.search(r'\b([1-9])\b', user_message)

            # Check if message looks like a selection
            if selection_match or (number_match and len(user_message) < 20):
                # Extract the selection number
                if selection_match:
                    selection = int(selection_match.group(1))
                else:
                    selection = int(number_match.group(1))

                # Validate selection is within range
                matches = pending_action.get('matches', [])
                if 1 <= selection <= len(matches):
                    # User made a valid selection - execute the pending action
                    selected_event = matches[selection - 1]
                    action = pending_action.get('action')
                    parsed_data = pending_action.get('parsed_data')

                    # Clear the pending action from session
                    session.pop('pending_action', None)

                    # Execute the action with the selected event ID
                    execution_result = None
                    try:
                        if action == 'delete':
                            execution_result = delete_event(user_id, {'event_id': selected_event['id']})

                        elif action == 'move':
                            execution_result = move_event(
                                user_id,
                                {'event_id': selected_event['id']},
                                parsed_data.get('new_date'),
                                parsed_data.get('new_time'),
                                parsed_data.get('new_end_time')
                            )

                        # Generate conversational response
                        conversational_message = generate_conversational_response(
                            action,
                            parsed_data,
                            execution_result
                        )

                        return jsonify({
                            'success': True,
                            'message': conversational_message,
                            'result': execution_result
                        }), 200

                    except Exception as e:
                        print(f"Error executing confirmed action: {str(e)}")
                        return jsonify({
                            'success': False,
                            'error': f'Failed to execute action: {str(e)}'
                        }), 500
                else:
                    # Invalid selection number
                    return jsonify({
                        'success': False,
                        'message': f'Invalid selection. Please choose a number between 1 and {len(matches)}.'
                    }), 400
            else:
                # User sent a new command instead of confirming - cancel pending action
                session.pop('pending_action', None)
                # Continue processing the new message as a fresh command below

        # Verify that the Groq API key is configured
        # Without this, we can't make AI requests
        if not Config.GROQ_API_KEY:
            return jsonify({
                'success': False,
                'error': 'Groq API key not configured'
            }), 500

        # Get today's date to provide context to the AI model
        # This allows the model to correctly interpret relative dates like:
        # - "tomorrow" (today + 1 day)
        # - "next Friday" (calculate from today)
        # - "in 3 days" (today + 3 days)
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')                # Format: 2026-02-28
        day_of_week = now.strftime('%A')                 # Format: Saturday
        current_year = now.year                          # Format: 2026

        # Calculate example dates for the prompt
        tomorrow = (now + timedelta(days=1)).strftime('%Y-%m-%d')
        # Find next Friday
        days_until_friday = (4 - now.weekday()) % 7  # 4 = Friday
        if days_until_friday == 0:
            days_until_friday = 7  # If today is Friday, get next Friday
        next_friday = (now + timedelta(days=days_until_friday)).strftime('%Y-%m-%d')
        # Find next Thursday
        days_until_thursday = (3 - now.weekday()) % 7  # 3 = Thursday
        if days_until_thursday == 0:
            days_until_thursday = 7  # If today is Thursday, get next Thursday
        next_thursday = (now + timedelta(days=days_until_thursday)).strftime('%Y-%m-%d')

        # Construct the system prompt for the AI model
        # This prompt is CRITICAL - it defines:
        # 1. What the AI's role is (calendar command parser)
        # 2. What format we expect (JSON only, no markdown)
        # 3. What actions are supported (create/delete/move/list)
        # 4. The exact JSON schema to return
        # 5. Examples of correct parsing
        system_prompt = f"""You are a calendar command parser. Today is {day_of_week}, {today}. The current year is {current_year}.

Your task is to parse natural language calendar commands into structured JSON. You must ONLY return valid JSON with no markdown, no code blocks, no explanations.

Supported actions:
- create: Schedule a new event
- delete: Cancel/remove an existing event
- move: Reschedule an event to a different time/date
- list: Show events for a specific date/period

Required JSON structure:
{{
  "action": "create|delete|move|list",
  "title": "event name or description",
  "date": "YYYY-MM-DD format",
  "time": "HH:MM in 24-hour format, or null if not specified",
  "end_time": "HH:MM in 24-hour format, or null if not specified",
  "new_date": "YYYY-MM-DD format for move action, or null otherwise",
  "new_time": "HH:MM in 24-hour format for move action, or null if not specified",
  "new_end_time": "HH:MM in 24-hour format for move action, or null if not specified",
  "confidence": 0.0 to 1.0 (how confident you are in parsing this command)
}}

Rules:
1. Convert relative dates (tomorrow, next Friday, etc.) to YYYY-MM-DD format based on today's date ({today})
2. IMPORTANT: When no year is specified, always use the current year ({current_year}), NOT previous years
3. Convert 12-hour time to 24-hour format (3pm → 15:00)
4. If time is not mentioned, set time to null
5. Parse end times and durations:
   - Explicit end time: "from 1pm to 3pm" → time: "13:00", end_time: "15:00"
   - Duration in hours: "2 hour meeting at 3pm" → time: "15:00", end_time: "17:00"
   - Duration in minutes: "30 minute call at 2pm" → time: "14:00", end_time: "14:30"
   - No duration specified → end_time: null (defaults to 1 hour)
6. For move actions, extract both original date/time/end_time and new date/time/end_time
7. For list actions, determine the date range they're asking about
8. Set confidence lower if the command is ambiguous
9. Extract event titles/descriptions from context
10. Return ONLY the JSON object, no other text

Examples:
Input: "schedule a meeting with John tomorrow at 3pm"
Output: {{"action": "create", "title": "meeting with John", "date": "{tomorrow}", "time": "15:00", "end_time": null, "new_date": null, "new_time": null, "new_end_time": null, "confidence": 0.95}}

Input: "book a conference room from 1pm to 3pm tomorrow"
Output: {{"action": "create", "title": "conference room", "date": "{tomorrow}", "time": "13:00", "end_time": "15:00", "new_date": null, "new_time": null, "new_end_time": null, "confidence": 0.95}}

Input: "schedule a 2 hour meeting at 3pm Friday"
Output: {{"action": "create", "title": "meeting", "date": "{next_friday}", "time": "15:00", "end_time": "17:00", "new_date": null, "new_time": null, "new_end_time": null, "confidence": 0.90}}

Input: "30 minute call with Sarah at 2pm tomorrow"
Output: {{"action": "create", "title": "call with Sarah", "date": "{tomorrow}", "time": "14:00", "end_time": "14:30", "new_date": null, "new_time": null, "new_end_time": null, "confidence": 0.95}}

Input: "cancel my dentist appointment Friday"
Output: {{"action": "delete", "title": "dentist appointment", "date": "{next_friday}", "time": null, "end_time": null, "new_date": null, "new_time": null, "new_end_time": null, "confidence": 0.85}}

Input: "move my 2pm meeting to Thursday at 4pm"
Output: {{"action": "move", "title": "2pm meeting", "date": "{today}", "time": "14:00", "end_time": null, "new_date": "{next_thursday}", "new_time": "16:00", "new_end_time": null, "confidence": 0.90}}

Input: "what do I have on Friday?"
Output: {{"action": "list", "title": "events", "date": "{next_friday}", "time": null, "end_time": null, "new_date": null, "new_time": null, "new_end_time": null, "confidence": 0.95}}"""

        # Call the Groq API to parse the natural language command
        # We use Llama 3.1 8B Instant - it's fast and accurate for structured tasks
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",         # System message defines the AI's behavior
                    "content": system_prompt  # Our detailed instructions (above)
                },
                {
                    "role": "user",           # User message is the actual input to parse
                    "content": user_message   # e.g., "schedule meeting tomorrow at 3pm"
                }
            ],
            model="llama-3.1-8b-instant",  # Fast model, good for structured tasks
            temperature=0.1,               # Low temperature = more deterministic/consistent
            max_tokens=500,                # Enough for our JSON response
            # CRITICAL: response_format forces the model to return valid JSON
            # Without this, the model might add markdown (```json) or explanations
            response_format={"type": "json_object"}
        )

        # Extract the AI's response from the completion object
        # The response is already guaranteed to be valid JSON (thanks to response_format)
        response_content = chat_completion.choices[0].message.content

        # Parse the JSON string into a Python dictionary
        parsed_data = json.loads(response_content)

        # PHASE 3C: Execute the parsed command on Google Calendar
        # Now that we've parsed the user's intent, we execute the actual calendar operation
        execution_result = None

        try:
            # Extract the action type from parsed data
            action = parsed_data.get('action')

            # Execute the appropriate calendar operation based on the action type
            if action == 'create':
                # Create a new calendar event
                # Event data includes: title, date, time (from parsed_data)
                execution_result = create_event(user_id, parsed_data)

            elif action == 'delete':
                # Delete a calendar event
                # IMPORTANT: If multiple events match, this returns a list for user confirmation
                # The frontend should show the list and let user choose which one to delete
                execution_result = delete_event(user_id, parsed_data)

            elif action == 'move':
                # Move/reschedule a calendar event
                # IMPORTANT: If multiple events match, this returns a list for user confirmation
                # The frontend should show the list and let user choose which one to move
                execution_result = move_event(
                    user_id,
                    parsed_data,
                    parsed_data.get('new_date'),
                    parsed_data.get('new_time'),
                    parsed_data.get('new_end_time')
                )

            elif action == 'list':
                # List events for a specific date or date range
                # Extract date and time from parsed_data
                execution_result = list_events(
                    user_id,
                    parsed_data.get('date'),
                    parsed_data.get('time')
                )

            else:
                # Unknown action type - this shouldn't happen if Groq is working correctly
                execution_result = {
                    'success': False,
                    'message': f'Unknown action: {action}'
                }

        except Exception as e:
            # If calendar operation fails, return error but keep parsed data
            # This allows frontend to show what we understood even if execution failed
            print(f"Error executing calendar action: {str(e)}")
            execution_result = {
                'success': False,
                'message': f'Failed to execute calendar action: {str(e)}'
            }

        # Generate a friendly, conversational response
        conversational_message = generate_conversational_response(
            action,
            parsed_data,
            execution_result
        )

        # ==================== STORE PENDING ACTION ====================
        # If execution resulted in multiple matches, store pending action in session
        if execution_result and execution_result.get('needs_confirmation') and execution_result.get('multiple_matches'):
            # Store the action, parsed data, and matches for confirmation
            session['pending_action'] = {
                'action': action,
                'parsed_data': parsed_data,
                'matches': execution_result['multiple_matches']
            }
        else:
            # Clear any pending action since this command was executed successfully
            session.pop('pending_action', None)

        # Return the conversational message and the execution result
        # The conversational message is what gets displayed to the user
        # The result data is available if the frontend needs it (e.g., for multiple matches)
        return jsonify({
            'success': True,
            'message': conversational_message,  # Friendly natural language response
            'result': execution_result          # Raw result data (for multiple matches, etc.)
        }), 200

    except json.JSONDecodeError as e:
        # This should rarely happen because response_format={"type": "json_object"}
        # guarantees valid JSON. But if it does happen, log details for debugging.
        print(f"JSON parsing error: {str(e)}")
        print(f"Response content: {response_content}")
        return jsonify({
            'success': False,
            'error': 'Failed to parse AI response'
        }), 500

    except Exception as e:
        # Catch any other unexpected errors (network issues, Groq API errors, etc.)
        # In production, use proper logging (e.g., Sentry) instead of print()
        print(f"Error processing message: {str(e)}")

        return jsonify({
            'success': False,
            'error': 'An error occurred processing your message'
        }), 500


# ==================== Calendar Endpoints ====================

@app.route('/api/calendar/events', methods=['GET'])
@require_auth  # Protected route - user must be logged in
@limiter.limit("60 per minute")
def get_calendar_events():
    """
    Fetch calendar events for a specific date range.

    This endpoint is used by the Calendar component to display events.
    It retrieves events from the user's Google Calendar within the specified
    time range and returns them in a format suitable for react-big-calendar.

    Query parameters:
    - start: ISO format datetime string (e.g., "2026-02-01T00:00:00")
    - end: ISO format datetime string (e.g., "2026-02-28T23:59:59")

    Returns:
    {
        "success": true,
        "events": [
            {
                "id": "event_id_from_google",
                "title": "Meeting with John",
                "start": "2026-02-27T15:00:00",
                "end": "2026-02-27T16:00:00",
                "description": "Discuss project updates"
            },
            ...
        ]
    }

    Error responses:
    - 400: Missing start or end parameters
    - 500: Failed to fetch events from Google Calendar
    """
    try:
        # Get the authenticated user's ID from the JWT
        user_id = g.user_id

        # Get query parameters for the date range
        # Frontend will pass these when calendar view changes (week/month/day)
        time_min = request.args.get('start')
        time_max = request.args.get('end')

        # Validate that both parameters are provided
        if not time_min or not time_max:
            return jsonify({
                'success': False,
                'error': 'Both start and end parameters are required'
            }), 400

        # Validate that start and end are valid ISO datetime format
        try:
            datetime.fromisoformat(time_min.replace('Z', '+00:00'))
            datetime.fromisoformat(time_max.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return jsonify({
                'success': False,
                'error': 'Invalid date format'
            }), 400

        # Fetch events from Google Calendar
        # get_all_events returns a list of event objects with id, title, start, end
        events = get_all_events(user_id, time_min, time_max)

        # Return the events to the frontend
        # The Calendar component will use these to render on the calendar view
        return jsonify({
            'success': True,
            'events': events
        }), 200

    except Exception as e:
        # If fetching events fails, log the error and return error response
        print(f"Error fetching calendar events: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch calendar events'
        }), 500


# ==================== Health Check Endpoint ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint to verify the server is running.

    Used by:
    - Monitoring systems (Render, Datadog, etc.)
    - Frontend to check if backend is available
    - Developers to test if server started successfully

    Returns:
        JSON with status message (always 200 OK if server is running)
    """
    return jsonify({
        'status': 'healthy',
        'message': 'JustScheduleIt backend is running'
    }), 200

# ==================== Server Startup ====================

if __name__ == '__main__':
    # This block only runs when the script is executed directly (not imported)
    # e.g., "python app.py"

    # Print startup information for debugging
    print(f"Starting Flask server on port {Config.PORT}...")
    print(f"Environment: {Config.FLASK_ENV}")
    print(f"CORS enabled for: {Config.CORS_ORIGINS}")

    # Start the Flask development server
    app.run(
        host='0.0.0.0',       # Listen on all network interfaces (allows external connections)
        port=Config.PORT,     # Port from config (default 5000)
        debug=Config.DEBUG    # Enable debug mode in development (hot reload, detailed errors)
    )
    # NOTE: In production (Render), use a production server like Gunicorn instead:
    # gunicorn app:app --bind 0.0.0.0:$PORT
