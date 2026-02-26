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
- /api/message - Parse calendar command with AI (protected)
- /api/health - Health check
"""

from flask import Flask, request, jsonify, g, make_response, redirect
from flask_cors import CORS
from config import Config
from groq import Groq
import json
from datetime import datetime

# Import authentication functions
# These handle Google OAuth flow and JWT session management
from auth import (
    get_google_auth_url,         # Generate OAuth URL to redirect user to Google
    exchange_code_for_tokens,    # Exchange OAuth code for access/refresh tokens
    get_google_user_info,        # Get user profile from Google
    create_jwt,                  # Create JWT for session management
    require_auth                 # Decorator to protect routes
)

# Import database functions
# These handle user and token storage in Supabase
from database import (
    get_user_by_google_id,  # Find user by their Google ID
    get_user_by_id,         # Find user by our internal UUID
    create_user,            # Create new user record
    store_refresh_token     # Store encrypted refresh token
)

# Initialize Flask application
app = Flask(__name__)

# Load configuration from Config class (which loads from .env)
app.config.from_object(Config)

# Enable CORS (Cross-Origin Resource Sharing) for frontend requests
# origins: Which domains can make requests to this API
# supports_credentials=True: Required to send/receive httpOnly cookies
# Without this, the browser won't send cookies in cross-origin requests
CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)

# Initialize Groq AI client for natural language processing
# Used to parse calendar commands like "schedule meeting tomorrow at 3pm"
groq_client = Groq(api_key=Config.GROQ_API_KEY)


# ==================== Authentication Endpoints ====================

@app.route('/api/auth/login', methods=['GET'])
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
            "new_date": "YYYY-MM-DD (move only) or null",
            "new_time": "HH:MM (move only) or null",
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

        user_message = data['message']

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
        today = datetime.now().strftime('%Y-%m-%d')       # Format: 2024-01-15
        day_of_week = datetime.now().strftime('%A')      # Format: Monday

        # Construct the system prompt for the AI model
        # This prompt is CRITICAL - it defines:
        # 1. What the AI's role is (calendar command parser)
        # 2. What format we expect (JSON only, no markdown)
        # 3. What actions are supported (create/delete/move/list)
        # 4. The exact JSON schema to return
        # 5. Examples of correct parsing
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

        # TODO Phase 3C: Execute the parsed command on Google Calendar
        # We'll:
        # 1. Get the user's encrypted refresh token from the database
        # 2. Use it to get a fresh access token
        # 3. Call the Google Calendar API to create/delete/move the event
        # 4. Return the result to the user
        #
        # refresh_token = get_refresh_token(user_id)
        # action_result = execute_calendar_action(refresh_token, parsed_data)

        # Return the parsed command structure to the frontend
        # Frontend can display what we understood from their command
        return jsonify({
            'success': True,
            'data': parsed_data
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
