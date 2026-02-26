"""
Configuration Module

Loads all configuration from environment variables (.env file).
This centralizes config and makes it easy to change between dev/prod environments.

SECURITY: Never commit the .env file to git! Only commit .env.example.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file into os.environ
# This must be called before accessing any env vars with os.getenv()
load_dotenv()

class Config:
    """
    Application configuration loaded from environment variables.

    All settings have defaults for development, but should be explicitly
    set in production for security and correctness.
    """

    # ==================== Flask Settings ====================

    # Environment: 'development' or 'production'
    # Affects debug mode and error verbosity
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')

    # Debug mode: Shows detailed error pages and enables hot reload
    # CRITICAL: Must be False in production for security
    DEBUG = FLASK_ENV == 'development'

    # Port to run the Flask server on
    # Default 5000 for development, but Render/Heroku will set this in production
    PORT = int(os.getenv('PORT', 5000))

    # ==================== CORS Settings ====================

    # Allowed origins for cross-origin requests
    # Development: Frontend dev server on localhost:5173
    # Production: Should be your Vercel domain (e.g., https://yourapp.vercel.app)
    # Multiple origins can be comma-separated: "http://localhost:5173,https://yourapp.vercel.app"
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')

    # ==================== API Keys ====================

    # Groq API key for Llama 3.1 natural language processing
    # Get from: https://console.groq.com/
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')

    # ==================== Database (Supabase) ====================

    # Supabase project URL
    # Format: https://xxxxx.supabase.co
    SUPABASE_URL = os.getenv('SUPABASE_URL')

    # Supabase service_role key (NOT the anon key!)
    # service_role bypasses Row Level Security - safe because it's server-side only
    # Get from: Project Settings → API → service_role key
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')

    # ==================== Google OAuth ====================

    # Google OAuth client ID
    # Get from: Google Cloud Console → Credentials
    # Format: xxxxx.apps.googleusercontent.com
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')

    # Google OAuth client secret
    # Keep this SECRET - never expose to frontend
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

    # OAuth callback URL - where Google redirects after user grants permissions
    # Must match exactly what's configured in Google Cloud Console
    # Development: http://localhost:5000/api/auth/callback
    # Production: https://yourbackend.onrender.com/api/auth/callback
    GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5000/api/auth/callback')

    # ==================== JWT Session Management ====================

    # Secret key for signing JWTs
    # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
    # Keep this SECRET - anyone with this key can create valid session tokens
    JWT_SECRET = os.getenv('JWT_SECRET')

    # JWT expiration time in seconds (default: 3600 = 1 hour)
    # After this time, the user must log in again
    JWT_EXPIRATION = int(os.getenv('JWT_EXPIRATION', 3600))

    # ==================== Encryption ====================

    # Fernet encryption key for encrypting refresh tokens in the database
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    # Keep this SECRET - anyone with this key can decrypt the stored refresh tokens
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
