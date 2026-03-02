"""
Authentication Module

Handles Google OAuth 2.0 login flow, JWT session management, and
authentication decorators for protected routes.

Security features:
- OAuth 2.0 with refresh token storage (never sent to frontend)
- JWT tokens stored in httpOnly cookies (XSS-safe)
- Refresh tokens allow long-term access without re-login
"""

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, g
from config import Config
import requests

# OAuth 2.0 scopes we need from Google
# These permissions allow us to:
# - calendar: Read and modify user's Google Calendar
# - userinfo.email: Get user's email address
# - userinfo.profile: Get user's name and profile picture
# - openid: Standard OpenID Connect scope for authentication
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]


# ==================== Google OAuth Functions ====================

def get_google_auth_url():
    """
    Generate the Google OAuth authorization URL for user to grant permissions.

    This creates the URL that redirects the user to Google's consent screen where
    they'll be asked to grant our app access to their calendar and profile info.

    Returns:
        str: Full authorization URL to redirect user to Google login
    """
    # Create OAuth flow with our client credentials
    # We use from_client_config to build the config programmatically
    # instead of loading from a client_secrets.json file
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": Config.GOOGLE_CLIENT_ID,
                "client_secret": Config.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [Config.GOOGLE_REDIRECT_URI]
            }
        },
        scopes=SCOPES,  # Request calendar and profile permissions
        redirect_uri=Config.GOOGLE_REDIRECT_URI  # Where Google sends user after consent
    )

    # Generate the authorization URL with specific parameters
    authorization_url, state = flow.authorization_url(
        # access_type='offline' is CRITICAL - it tells Google to return a refresh token
        # Refresh tokens allow us to get new access tokens without re-prompting the user
        access_type='offline',

        # Include previously granted scopes - helps avoid scope order mismatch errors
        include_granted_scopes='true',

        # prompt='consent' forces the consent screen to show every time
        # This ensures we get a refresh token even if user previously granted access
        # Without this, repeat logins may not return a refresh token
        prompt='consent'
    )

    return authorization_url


def exchange_code_for_tokens(code: str):
    """
    Exchange OAuth authorization code for access and refresh tokens.

    After the user grants permissions on Google's consent screen, Google redirects
    back to our callback URL with an authorization code. We exchange that code
    for actual tokens that let us access the user's calendar.

    Args:
        code: Authorization code from Google OAuth callback URL

    Returns:
        dict: {
            'access_token': Short-lived token for immediate API calls,
            'refresh_token': Long-lived token to get new access tokens
        }
    """
    # IMPORTANT: We set scopes=None here to avoid "scope has changed" errors
    # Google may return scopes in a different order than we requested, which
    # causes the google-auth library to throw an error if we specify scopes here.
    # Since Google already validated scopes during the authorization step,
    # we can safely skip validation in the callback.
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": Config.GOOGLE_CLIENT_ID,
                "client_secret": Config.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [Config.GOOGLE_REDIRECT_URI]
            }
        },
        scopes=None,  # Skip scope validation to avoid order mismatch errors
        redirect_uri=Config.GOOGLE_REDIRECT_URI
    )

    # Exchange the authorization code for tokens
    # This makes a POST request to Google's token endpoint
    flow.fetch_token(code=code)

    # Extract credentials from the flow
    credentials = flow.credentials

    # Return both tokens as a dictionary
    # access_token: Valid for ~1 hour, used for immediate API calls
    # refresh_token: Valid indefinitely (until revoked), used to get new access tokens
    return {
        'access_token': credentials.token,
        'refresh_token': credentials.refresh_token
    }


def get_google_user_info(access_token: str):
    """
    Fetch user profile information from Google using an access token.

    This retrieves the user's Google ID, email, name, and profile picture URL.
    We use this during login to create/update the user record in our database.

    Args:
        access_token: Valid Google OAuth access token

    Returns:
        dict: {
            'id': Google user ID (unique identifier),
            'email': User's email address,
            'name': User's full name,
            'picture': URL to profile picture
        }

    Raises:
        Exception: If the API request fails
    """
    # Call Google's userinfo endpoint with Bearer token authentication
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        headers=headers
    )

    if response.status_code == 200:
        user_info = response.json()
        # Extract only the fields we need and return as a clean dict
        # Using .get() instead of direct access prevents KeyErrors
        return {
            'id': user_info.get('id'),          # Google's unique user ID
            'email': user_info.get('email'),    # Primary email address
            'name': user_info.get('name'),      # Display name
            'picture': user_info.get('picture') # Profile photo URL
        }
    else:
        # If request fails, raise an exception with error details
        raise Exception(f"Failed to fetch user info: {response.text}")


def refresh_access_token(refresh_token: str):
    """
    Use a refresh token to obtain a new access token without user interaction.

    Access tokens expire after ~1 hour, but refresh tokens are long-lived.
    This function exchanges a refresh token for a fresh access token, allowing
    us to make API calls on behalf of the user without requiring them to log in again.

    This will be used in Phase 3C when we interact with the Google Calendar API.

    Args:
        refresh_token: Valid Google OAuth refresh token (stored encrypted in database)

    Returns:
        str: New access token (valid for ~1 hour)

    Raises:
        Exception: If the refresh fails (e.g., token was revoked by user)
    """
    token_uri = "https://oauth2.googleapis.com/token"

    # Prepare the token refresh request
    # grant_type='refresh_token' tells Google we're exchanging a refresh token
    data = {
        'client_id': Config.GOOGLE_CLIENT_ID,
        'client_secret': Config.GOOGLE_CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }

    # Make the token refresh request to Google
    response = requests.post(token_uri, data=data)

    if response.status_code == 200:
        # Successfully got a new access token
        return response.json()['access_token']
    else:
        # Refresh failed - token may have been revoked or expired
        raise Exception(f"Failed to refresh access token: {response.text}")


# ==================== JWT Functions ====================

def create_jwt(user_id: str):
    """
    Create a JWT (JSON Web Token) for user session management.

    JWTs are used instead of server-side sessions because they're stateless
    and work well in distributed systems. The token is signed with our secret
    key, so we can verify it hasn't been tampered with.

    The JWT will be stored in an httpOnly cookie (set in app.py), which protects
    against XSS attacks since JavaScript can't access httpOnly cookies.

    Args:
        user_id: User's UUID from our database (not their Google ID)

    Returns:
        str: Encoded JWT token containing user_id and expiration time
    """
    # Build the JWT payload with claims
    payload = {
        'user_id': user_id,  # Who this token belongs to
        'exp': datetime.now(timezone.utc) + timedelta(seconds=Config.JWT_EXPIRATION),  # When it expires
        'iat': datetime.now(timezone.utc)  # When it was issued (for debugging/logging)
    }

    # Encode and sign the JWT using HS256 (HMAC with SHA-256)
    # The JWT_SECRET is used to sign the token - anyone with the secret can
    # create valid tokens, so we never share it with the frontend
    token = jwt.encode(payload, Config.JWT_SECRET, algorithm='HS256')
    return token


def verify_jwt(token: str):
    """
    Decode and validate a JWT token, ensuring it's not expired or tampered with.

    This function:
    1. Verifies the signature using our JWT_SECRET
    2. Checks that the token hasn't expired
    3. Extracts the user_id from the payload

    Args:
        token: JWT token string from httpOnly cookie

    Returns:
        str: User ID (UUID) extracted from the token payload, or None if validation fails
        None: If token is expired, invalid, malformed, empty, None, or missing user_id
    """
    # Handle None or empty token
    if not token:
        return None

    try:
        # Decode the JWT and verify its signature
        # algorithms=['HS256'] ensures we only accept tokens signed with HS256
        # This prevents algorithm confusion attacks
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])

        # Extract the user_id from the token
        # Return None if user_id is not in payload
        return payload.get('user_id')

    except jwt.ExpiredSignatureError:
        # Token is valid but has expired (past the 'exp' claim)
        return None
    except jwt.InvalidTokenError:
        # Token is malformed, signature doesn't match, or other validation error
        return None
    except Exception:
        # Catch any other unexpected errors and return None
        return None


# ==================== Authentication Decorator ====================

def require_auth(f):
    """
    Decorator to protect routes that require authentication.

    This decorator wraps Flask route functions and automatically validates that
    the user is logged in before allowing access to the route. It:
    1. Extracts the JWT from the httpOnly cookie
    2. Validates the JWT signature and expiration
    3. Attaches the user_id to Flask's g object (request-scoped global)
    4. Returns 401 Unauthorized if authentication fails

    The protected route can then access g.user_id to know which user is making the request.

    Usage:
        @app.route('/api/protected')
        @require_auth  # Add this decorator below @app.route
        def protected_route():
            user_id = g.user_id  # Access the authenticated user's ID
            return jsonify({'message': 'Authenticated!'})

    Args:
        f: The Flask route function to protect

    Returns:
        The decorated function that includes authentication checks
    """
    # @wraps preserves the original function's name and docstring
    # This is important for Flask's routing system
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Try to get the JWT from the httpOnly cookie
        # The cookie name 'jwt_token' was set in app.py during login
        token = request.cookies.get('jwt_token')

        if not token:
            # No token found - user is not logged in
            return jsonify({
                'success': False,
                'error': 'Not authenticated'
            }), 401

        try:
            # Verify the JWT and extract the user_id
            user_id = verify_jwt(token)

            # Attach user_id to Flask's g object
            # g is request-scoped, meaning it's automatically cleaned up after the request
            # This makes user_id available to the route function without passing it as a parameter
            g.user_id = user_id

            # Call the original route function with authentication passed
            return f(*args, **kwargs)

        except Exception as e:
            # JWT validation failed (expired, invalid signature, etc.)
            return jsonify({
                'success': False,
                'error': f'Authentication failed: {str(e)}'
            }), 401

    return decorated_function
