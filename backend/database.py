"""
Database Module

Handles all database operations using Supabase (PostgreSQL).
Includes encryption/decryption of sensitive tokens and CRUD operations for users.

Security:
- Uses service_role key (bypasses Row Level Security) - safe because this only runs server-side
- Refresh tokens are encrypted with Fernet before storage
- All database queries are parameterized (Supabase SDK handles this automatically)
"""

from supabase import create_client, Client
from cryptography.fernet import Fernet
from config import Config
from datetime import datetime

# Initialize Supabase client with our project URL and service_role key
# service_role key gives full admin access and bypasses Row Level Security (RLS)
# This is safe because this code only runs server-side, never on the frontend
supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

# Initialize Fernet cipher for symmetric encryption of refresh tokens
# Fernet uses AES-128 in CBC mode with PKCS7 padding
# The ENCRYPTION_KEY is a base64-encoded 32-byte key generated with Fernet.generate_key()
# Even if someone gains access to our database, they can't use the tokens without this key
cipher = Fernet(Config.ENCRYPTION_KEY.encode())


# ==================== Encryption Functions ====================

def encrypt_token(token: str) -> str:
    """
    Encrypt a refresh token using Fernet symmetric encryption.

    Refresh tokens are extremely sensitive - they allow indefinite access to
    a user's Google Calendar. We encrypt them before storing in the database so
    that even if our database is compromised, the tokens are useless without
    the ENCRYPTION_KEY (which is stored in environment variables, not the database).

    Args:
        token: Plain text refresh token from Google OAuth

    Returns:
        str: Base64-encoded encrypted token (safe to store in database)
    """
    # cipher.encrypt() returns bytes, we decode to string for database storage
    return cipher.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a refresh token to use for Google API calls.

    This is only called when we need to make Calendar API requests on behalf
    of the user. The decrypted token is never sent to the frontend or logged.

    Args:
        encrypted_token: Base64-encoded encrypted token from database

    Returns:
        str: Plain text refresh token ready to use with Google APIs
    """
    # cipher.decrypt() expects bytes, returns bytes, we decode to string
    return cipher.decrypt(encrypted_token.encode()).decode()


# ==================== User Operations ====================

def get_user_by_google_id(google_id: str):
    """
    Find a user by their Google ID.

    We use Google ID (not email) as the unique identifier because:
    - Email addresses can change (user updates their Google account)
    - Google IDs are permanent and never change
    - This prevents issues when users change their email

    Used during login to check if the user already exists in our database.

    Args:
        google_id: Unique Google user identifier (looks like a long number string)

    Returns:
        dict: User record with all fields, or None if not found
    """
    try:
        # Query the users table for a matching google_id
        # .eq() creates a parameterized query (safe from SQL injection)
        response = supabase.table('users')\
            .select('*')\
            .eq('google_id', google_id)\
            .execute()

        # Check if we got any results
        if response.data and len(response.data) > 0:
            return response.data[0]  # Return the first (and only) match
        return None
    except Exception as e:
        # Log the error but don't expose internal details to the caller
        print(f"Error fetching user by Google ID: {str(e)}")
        return None


def get_user_by_id(user_id: str):
    """
    Find a user by their database UUID.

    This is different from get_user_by_google_id:
    - user_id is our internal database primary key (UUID)
    - google_id is Google's identifier for the user

    Used by protected endpoints to fetch user data based on the JWT token,
    which contains our internal user_id.

    Args:
        user_id: UUID from our users table (stored in JWT)

    Returns:
        dict: User record with all fields, or None if not found
    """
    try:
        response = supabase.table('users')\
            .select('*')\
            .eq('id', user_id)\
            .execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error fetching user by ID: {str(e)}")
        return None


def create_user(google_id: str, email: str, name: str, picture: str):
    """
    Create a new user in the database after their first Google login.

    This is called during the OAuth callback if the user doesn't exist yet.
    Supabase automatically generates the UUID for the 'id' field and sets
    created_at/updated_at timestamps.

    Args:
        google_id: User's Google ID (permanent identifier from Google)
        email: User's email address
        name: User's display name from Google profile
        picture: URL to user's Google profile picture

    Returns:
        dict: Newly created user record, or None if creation failed
    """
    try:
        # Insert new user with Google profile data
        # Supabase handles the id (UUID) and timestamps automatically
        response = supabase.table('users').insert({
            'google_id': google_id,
            'email': email,
            'name': name,
            'picture': picture
        }).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]  # Return the created user record
        return None
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        return None


def update_user(user_id: str, data: dict):
    """
    Update user information (e.g., if they change their name/email on Google).

    Currently not used, but available for future features where we might
    sync user profile changes from Google.

    Args:
        user_id: UUID of the user to update
        data: Dictionary of fields to update (e.g., {'name': 'New Name'})

    Returns:
        dict: Updated user record, or None if update failed
    """
    try:
        # Automatically update the updated_at timestamp
        data['updated_at'] = datetime.utcnow().isoformat()

        response = supabase.table('users')\
            .update(data)\
            .eq('id', user_id)\
            .execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error updating user: {str(e)}")
        return None


# ==================== Refresh Token Operations ====================

def store_refresh_token(user_id: str, refresh_token: str):
    """
    Encrypt and store a Google OAuth refresh token for a user.

    CRITICAL SECURITY FUNCTION:
    - Refresh tokens allow long-term access to user's Google Calendar
    - We NEVER send refresh tokens to the frontend
    - They are encrypted before storage using Fernet
    - Only this server can decrypt them (using ENCRYPTION_KEY)

    The function handles both new users (insert) and returning users (update).
    Each user can only have one refresh token at a time (enforced by database constraint).

    Args:
        user_id: UUID of the user who owns this token
        refresh_token: Plain text refresh token from Google OAuth

    Returns:
        bool: True if storage succeeded, False otherwise
    """
    try:
        # Encrypt the token before storing
        # This protects it even if the database is compromised
        encrypted = encrypt_token(refresh_token)

        # Check if this user already has a token stored
        # (e.g., they logged in before and are logging in again)
        existing = supabase.table('refresh_tokens')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()

        if existing.data and len(existing.data) > 0:
            # User already exists - update their token
            # This happens when:
            # - User logs in again (gets a new refresh token)
            # - Token is refreshed (though Google usually keeps the same one)
            response = supabase.table('refresh_tokens')\
                .update({
                    'encrypted_token': encrypted,
                    'updated_at': datetime.utcnow().isoformat()
                })\
                .eq('user_id', user_id)\
                .execute()
        else:
            # First time seeing this user - insert new token record
            response = supabase.table('refresh_tokens').insert({
                'user_id': user_id,
                'encrypted_token': encrypted
            }).execute()

        return True
    except Exception as e:
        # If storage fails, the user won't be able to use calendar features
        # We log the error but don't expose details to the caller
        print(f"Error storing refresh token: {str(e)}")
        return False


def get_refresh_token(user_id: str):
    """
    Retrieve and decrypt a user's Google refresh token.

    This is called when we need to make Google Calendar API requests on behalf
    of the user (Phase 3C). The decrypted token is used to get a fresh access token.

    SECURITY NOTE: The decrypted token is only used server-side and is NEVER
    sent to the frontend or logged. It stays in memory briefly for the API call.

    Args:
        user_id: UUID of the user whose token we need

    Returns:
        str: Decrypted refresh token ready to use with Google APIs,
             or None if no token found (user never logged in)
    """
    try:
        # Fetch only the encrypted_token field (no need for other columns)
        response = supabase.table('refresh_tokens')\
            .select('encrypted_token')\
            .eq('user_id', user_id)\
            .execute()

        if response.data and len(response.data) > 0:
            # Get the encrypted token from the database
            encrypted = response.data[0]['encrypted_token']

            # Decrypt it using our Fernet cipher
            # The decrypted token is only returned, never logged or stored
            return decrypt_token(encrypted)
        return None  # User has no refresh token stored
    except Exception as e:
        print(f"Error retrieving refresh token: {str(e)}")
        return None


def delete_refresh_token(user_id: str):
    """
    Remove a user's refresh token (used during logout or token revocation).

    This prevents any future use of the refresh token. The user will need to
    log in again (go through OAuth flow) to get a new refresh token.

    Note: This doesn't revoke the token with Google - it just removes our copy.
    The token is still technically valid on Google's side until it expires or
    the user revokes it in their Google Account settings.

    Args:
        user_id: UUID of the user whose token should be deleted

    Returns:
        bool: True if deletion succeeded, False otherwise
    """
    try:
        # Delete the token record for this user
        # ON DELETE CASCADE in the database will handle cleanup if user is deleted
        supabase.table('refresh_tokens')\
            .delete()\
            .eq('user_id', user_id)\
            .execute()
        return True
    except Exception as e:
        print(f"Error deleting refresh token: {str(e)}")
        return False
