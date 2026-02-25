from flask import Flask, request, jsonify, g, make_response, redirect
from flask_cors import CORS
from config import Config
from groq import Groq
import json
from datetime import datetime

# Import auth and database modules
from auth import (
    get_google_auth_url,
    exchange_code_for_tokens,
    get_google_user_info,
    create_jwt,
    require_auth
)
from database import (
    get_user_by_google_id,
    get_user_by_id,
    create_user,
    store_refresh_token
)

# Initialize Flask app
app = Flask(__name__)

# Load configuration
app.config.from_object(Config)

# Enable CORS for cross-origin requests from frontend
# Important: supports_credentials=True is required for httpOnly cookies
CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)

# Initialize Groq client
groq_client = Groq(api_key=Config.GROQ_API_KEY)


# ==================== Authentication Endpoints ====================

@app.route('/api/auth/login', methods=['GET'])
def login():
    """
    Initiate Google OAuth flow.
    Redirects user to Google consent screen.
    """
    try:
        auth_url = get_google_auth_url()
        return redirect(auth_url)
    except Exception as e:
        print(f"Error initiating login: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to initiate login'
        }), 500


@app.route('/api/auth/callback', methods=['GET'])
def auth_callback():
    """
    Handle Google OAuth callback.
    Exchanges code for tokens, creates/updates user, issues JWT cookie.
    """
    try:
        # Get authorization code from query params
        code = request.args.get('code')

        if not code:
            return jsonify({
                'success': False,
                'error': 'No authorization code provided'
            }), 400

        # Exchange code for access and refresh tokens
        tokens = exchange_code_for_tokens(code)
        access_token = tokens['access_token']
        refresh_token = tokens['refresh_token']

        # Get user info from Google
        user_info = get_google_user_info(access_token)

        # Create or update user in database
        user = get_user_by_google_id(user_info['id'])
        if not user:
            user = create_user(
                google_id=user_info['id'],
                email=user_info['email'],
                name=user_info['name'],
                picture=user_info['picture']
            )

        # Store encrypted refresh token
        store_refresh_token(user['id'], refresh_token)

        # Create JWT for session
        jwt_token = create_jwt(user['id'])

        # Set httpOnly cookie and redirect to frontend dashboard
        response = make_response(redirect('http://localhost:5173/dashboard'))
        response.set_cookie(
            'jwt_token',
            value=jwt_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite='Lax',
            max_age=Config.JWT_EXPIRATION
        )

        return response

    except Exception as e:
        print(f"Error in auth callback: {str(e)}")
        # Redirect to frontend with error
        return redirect('http://localhost:5173?error=auth_failed')


@app.route('/api/auth/user', methods=['GET'])
@require_auth
def get_current_user():
    """
    Get current authenticated user's information.
    Protected route - requires valid JWT cookie.
    """
    try:
        user_id = g.user_id  # Set by @require_auth decorator
        user = get_user_by_id(user_id)

        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'picture': user['picture']
            }
        }), 200

    except Exception as e:
        print(f"Error fetching user: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch user'
        }), 500


@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    """
    Logout user by clearing JWT cookie.
    Protected route - requires valid JWT cookie.
    """
    try:
        response = make_response(jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }))

        # Delete the JWT cookie
        response.delete_cookie('jwt_token')

        return response

    except Exception as e:
        print(f"Error during logout: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to logout'
        }), 500


# ==================== Message Endpoint ====================

@app.route('/api/message', methods=['POST'])
@require_auth  # Now requires authentication!
def handle_message():
    """
    Handle incoming messages from the frontend.
    Phase 3A: Now requires authentication.
    Parse natural language calendar commands using Groq API.

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
            "new_date": "YYYY-MM-DD (move only) or null",
            "new_time": "HH:MM (move only) or null",
            "confidence": 0.95
        }
    }
    """
    try:
        # Get authenticated user ID
        user_id = g.user_id  # Set by @require_auth decorator
        # Get JSON data from request
        data = request.get_json()

        # Validate that message field exists
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Message field is required'
            }), 400

        user_message = data['message']

        # Validate API key is configured
        if not Config.GROQ_API_KEY:
            return jsonify({
                'success': False,
                'error': 'Groq API key not configured'
            }), 500

        # Get today's date for context
        today = datetime.now().strftime('%Y-%m-%d')
        day_of_week = datetime.now().strftime('%A')

        # System prompt for Groq API
        system_prompt = f"""You are a calendar command parser. Today is {day_of_week}, {today}.

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
  "new_date": "YYYY-MM-DD format for move action, or null otherwise",
  "new_time": "HH:MM in 24-hour format for move action, or null if not specified",
  "confidence": 0.0 to 1.0 (how confident you are in parsing this command)
}}

Rules:
1. Convert relative dates (tomorrow, next Friday, etc.) to YYYY-MM-DD format based on today's date
2. Convert 12-hour time to 24-hour format (3pm → 15:00)
3. If time is not mentioned, set time to null
4. For move actions, extract both original date/time and new date/time
5. For list actions, determine the date range they're asking about
6. Set confidence lower if the command is ambiguous
7. Extract event titles/descriptions from context
8. Return ONLY the JSON object, no other text

Examples:
Input: "schedule a meeting with John tomorrow at 3pm"
Output: {{"action": "create", "title": "meeting with John", "date": "2024-01-15", "time": "15:00", "new_date": null, "new_time": null, "confidence": 0.95}}

Input: "cancel my dentist appointment Friday"
Output: {{"action": "delete", "title": "dentist appointment", "date": "2024-01-19", "time": null, "new_date": null, "new_time": null, "confidence": 0.85}}

Input: "move my 2pm meeting to Thursday at 4pm"
Output: {{"action": "move", "title": "2pm meeting", "date": "{today}", "time": "14:00", "new_date": "2024-01-18", "new_time": "16:00", "confidence": 0.90}}

Input: "what do I have on Friday?"
Output: {{"action": "list", "title": "events", "date": "2024-01-19", "time": null, "new_date": null, "new_time": null, "confidence": 0.95}}"""

        # Call Groq API with JSON mode enabled
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0.1,
            max_tokens=500,
            response_format={"type": "json_object"}  # Forces JSON response
        )

        # Extract and parse the JSON response
        response_content = chat_completion.choices[0].message.content
        parsed_data = json.loads(response_content)

        # TODO Phase 3C: Execute calendar action using Google Calendar API
        # refresh_token = get_refresh_token(user_id)
        # action_result = execute_calendar_action(refresh_token, parsed_data)

        return jsonify({
            'success': True,
            'data': parsed_data
        }), 200

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {str(e)}")
        print(f"Response content: {response_content}")
        return jsonify({
            'success': False,
            'error': 'Failed to parse AI response'
        }), 500

    except Exception as e:
        # Log error (in production, use proper logging)
        print(f"Error processing message: {str(e)}")

        return jsonify({
            'success': False,
            'error': 'An error occurred processing your message'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'JustScheduleIt backend is running'
    }), 200

if __name__ == '__main__':
    print(f"Starting Flask server on port {Config.PORT}...")
    print(f"Environment: {Config.FLASK_ENV}")
    print(f"CORS enabled for: {Config.CORS_ORIGINS}")

    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    )
