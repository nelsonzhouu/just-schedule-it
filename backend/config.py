import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration"""
    # Flask settings
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    PORT = int(os.getenv('PORT', 5000))

    # CORS settings
    # In development, allow frontend dev server
    # In production, this should be set to your Vercel frontend URL
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')

    # API Keys
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')

    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5000/api/auth/callback')

    # JWT Configuration
    JWT_SECRET = os.getenv('JWT_SECRET')
    JWT_EXPIRATION = int(os.getenv('JWT_EXPIRATION', 3600))

    # Encryption
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
