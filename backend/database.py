from supabase import create_client, Client
from cryptography.fernet import Fernet
from config import Config
from datetime import datetime

# Initialize Supabase client
supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

# Initialize Fernet cipher for encryption
cipher = Fernet(Config.ENCRYPTION_KEY.encode())


# ==================== Encryption Functions ====================

def encrypt_token(token: str) -> str:
    """Encrypt a refresh token using Fernet symmetric encryption"""
    return cipher.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a refresh token using Fernet"""
    return cipher.decrypt(encrypted_token.encode()).decode()


# ==================== User Operations ====================

def get_user_by_google_id(google_id: str):
    """Find a user by their Google ID"""
    try:
        response = supabase.table('users')\
            .select('*')\
            .eq('google_id', google_id)\
            .execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error fetching user by Google ID: {str(e)}")
        return None


def get_user_by_id(user_id: str):
    """Find a user by their UUID"""
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
    """Create a new user in the database"""
    try:
        response = supabase.table('users').insert({
            'google_id': google_id,
            'email': email,
            'name': name,
            'picture': picture
        }).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        return None


def update_user(user_id: str, data: dict):
    """Update user information"""
    try:
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
    """Encrypt and store Google refresh token"""
    try:
        encrypted = encrypt_token(refresh_token)

        # Check if token already exists for this user
        existing = supabase.table('refresh_tokens')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()

        if existing.data and len(existing.data) > 0:
            # Update existing token
            response = supabase.table('refresh_tokens')\
                .update({
                    'encrypted_token': encrypted,
                    'updated_at': datetime.utcnow().isoformat()
                })\
                .eq('user_id', user_id)\
                .execute()
        else:
            # Insert new token
            response = supabase.table('refresh_tokens').insert({
                'user_id': user_id,
                'encrypted_token': encrypted
            }).execute()

        return True
    except Exception as e:
        print(f"Error storing refresh token: {str(e)}")
        return False


def get_refresh_token(user_id: str):
    """Retrieve and decrypt Google refresh token"""
    try:
        response = supabase.table('refresh_tokens')\
            .select('encrypted_token')\
            .eq('user_id', user_id)\
            .execute()

        if response.data and len(response.data) > 0:
            encrypted = response.data[0]['encrypted_token']
            return decrypt_token(encrypted)
        return None
    except Exception as e:
        print(f"Error retrieving refresh token: {str(e)}")
        return None


def delete_refresh_token(user_id: str):
    """Remove refresh token for a user (logout)"""
    try:
        supabase.table('refresh_tokens')\
            .delete()\
            .eq('user_id', user_id)\
            .execute()
        return True
    except Exception as e:
        print(f"Error deleting refresh token: {str(e)}")
        return False
