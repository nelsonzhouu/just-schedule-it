from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from config import Config
import requests

# OAuth 2.0 scopes we need
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]


# ==================== Google OAuth Functions ====================

def get_google_auth_url():
    """
    Generate the Google OAuth authorization URL.
    Returns the URL to redirect the user to for consent.
    """
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
        scopes=SCOPES,
        redirect_uri=Config.GOOGLE_REDIRECT_URI
    )

    authorization_url, state = flow.authorization_url(
        access_type='offline',  # Request refresh token
        include_granted_scopes='true',
        prompt='consent'  # Force consent screen to get refresh token
    )

    return authorization_url


def exchange_code_for_tokens(code: str):
    """
    Exchange OAuth authorization code for access and refresh tokens.

    Args:
        code: Authorization code from Google OAuth callback

    Returns:
        dict: {'access_token': '...', 'refresh_token': '...'}
    """
    # Don't specify scopes in callback flow to avoid scope order mismatch errors
    # Google already validated scopes during authorization
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
        scopes=None,  # Don't validate scopes in callback
        redirect_uri=Config.GOOGLE_REDIRECT_URI
    )

    flow.fetch_token(code=code)

    credentials = flow.credentials

    return {
        'access_token': credentials.token,
        'refresh_token': credentials.refresh_token
    }


def get_google_user_info(access_token: str):
    """
    Fetch user profile information from Google.

    Args:
        access_token: Google OAuth access token

    Returns:
        dict: {'id': '...', 'email': '...', 'name': '...', 'picture': '...'}
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        headers=headers
    )

    if response.status_code == 200:
        user_info = response.json()
        return {
            'id': user_info.get('id'),
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture')
        }
    else:
        raise Exception(f"Failed to fetch user info: {response.text}")


def refresh_access_token(refresh_token: str):
    """
    Use a refresh token to get a new access token.

    Args:
        refresh_token: Google OAuth refresh token

    Returns:
        str: New access token
    """
    token_uri = "https://oauth2.googleapis.com/token"
    data = {
        'client_id': Config.GOOGLE_CLIENT_ID,
        'client_secret': Config.GOOGLE_CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }

    response = requests.post(token_uri, data=data)

    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Failed to refresh access token: {response.text}")


# ==================== JWT Functions ====================

def create_jwt(user_id: str):
    """
    Create a JWT token for a user session.

    Args:
        user_id: User's UUID from database

    Returns:
        str: Encoded JWT token
    """
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=Config.JWT_EXPIRATION),
        'iat': datetime.utcnow()
    }

    token = jwt.encode(payload, Config.JWT_SECRET, algorithm='HS256')
    return token


def verify_jwt(token: str):
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        str: User ID from token payload

    Raises:
        jwt.ExpiredSignatureError: If token is expired
        jwt.InvalidTokenError: If token is invalid
    """
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        raise Exception('Token has expired')
    except jwt.InvalidTokenError:
        raise Exception('Invalid token')


# ==================== Authentication Decorator ====================

def require_auth(f):
    """
    Decorator to protect routes that require authentication.
    Validates JWT from httpOnly cookie and attaches user_id to request context.

    Usage:
        @app.route('/api/protected')
        @require_auth
        def protected_route():
            user_id = g.user_id
            return jsonify({'message': 'Authenticated!'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get JWT from httpOnly cookie
        token = request.cookies.get('jwt_token')

        if not token:
            return jsonify({
                'success': False,
                'error': 'Not authenticated'
            }), 401

        try:
            # Verify and decode JWT
            user_id = verify_jwt(token)

            # Attach user_id to Flask's request context
            g.user_id = user_id

            # Call the original route function
            return f(*args, **kwargs)

        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Authentication failed: {str(e)}'
            }), 401

    return decorated_function
