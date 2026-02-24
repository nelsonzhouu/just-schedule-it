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

    # Future: Add additional secrets here
    # SUPABASE_URL = os.getenv('SUPABASE_URL')
    # SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    # JWT_SECRET = os.getenv('JWT_SECRET')
