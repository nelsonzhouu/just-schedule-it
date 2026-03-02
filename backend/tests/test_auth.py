"""
Unit tests for auth.py

Tests critical authentication functions:
- create_jwt() - JWT token creation
- verify_jwt() - JWT token verification
"""

import pytest
import jwt
import time
from datetime import datetime, timedelta, timezone
import sys
import os

# Add parent directory to path so we can import auth
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth import create_jwt, verify_jwt
from config import Config


# ==================== Tests for create_jwt() ====================

class TestCreateJWT:
    """Test create_jwt() function for JWT token creation."""

    def test_creates_valid_jwt(self):
        """Test that create_jwt returns a valid JWT token string."""
        user_id = "test_user_123"
        token = create_jwt(user_id)

        # Should return a string
        assert isinstance(token, str)
        # JWT tokens have 3 parts separated by dots
        assert len(token.split('.')) == 3

    def test_payload_contains_user_id(self):
        """Test that JWT payload contains the user_id."""
        user_id = "test_user_456"
        token = create_jwt(user_id)

        # Decode without verification to check payload
        payload = jwt.decode(token, options={"verify_signature": False})

        assert payload['user_id'] == user_id

    def test_payload_contains_expiration(self):
        """Test that JWT payload contains expiration time."""
        user_id = "test_user_789"
        token = create_jwt(user_id)

        # Decode without verification to check payload
        payload = jwt.decode(token, options={"verify_signature": False})

        # Should have 'exp' field
        assert 'exp' in payload

        # Expiration should be in the future
        current_time = datetime.now(timezone.utc).timestamp()
        assert payload['exp'] > current_time

    def test_expiration_is_correct_duration(self):
        """Test that JWT expiration is set to JWT_EXPIRATION seconds."""
        user_id = "test_user_abc"
        token = create_jwt(user_id)

        # Decode without verification to check payload
        payload = jwt.decode(token, options={"verify_signature": False})

        # Calculate expected expiration
        current_time = datetime.now(timezone.utc)
        expected_exp = current_time + timedelta(seconds=Config.JWT_EXPIRATION)

        # Allow 2 second tolerance for test execution time
        assert abs(payload['exp'] - expected_exp.timestamp()) < 2

    def test_different_users_get_different_tokens(self):
        """Test that different user IDs produce different tokens."""
        token1 = create_jwt("user_1")
        token2 = create_jwt("user_2")

        # Tokens should be different
        assert token1 != token2

        # But should both be valid JWT format
        assert len(token1.split('.')) == 3
        assert len(token2.split('.')) == 3


# ==================== Tests for verify_jwt() ====================

class TestVerifyJWT:
    """Test verify_jwt() function for JWT token verification."""

    def test_verify_valid_token_returns_user_id(self):
        """Test that verifying a valid token returns the user_id."""
        user_id = "test_user_valid"
        token = create_jwt(user_id)

        # Verify the token
        result = verify_jwt(token)

        # Should return the user_id
        assert result == user_id

    def test_verify_expired_token_returns_none(self):
        """Test that verifying an expired token returns None."""
        user_id = "test_user_expired"

        # Create a token with -1 second expiration (already expired)
        payload = {
            'user_id': user_id,
            'exp': datetime.now(timezone.utc) + timedelta(seconds=-1)
        }
        expired_token = jwt.encode(payload, Config.JWT_SECRET, algorithm='HS256')

        # Wait a moment to ensure it's definitely expired
        time.sleep(0.1)

        # Verify should return None
        result = verify_jwt(expired_token)
        assert result is None

    def test_verify_invalid_signature_returns_none(self):
        """Test that verifying a token with wrong signature returns None."""
        user_id = "test_user_invalid"

        # Create a token with wrong secret
        payload = {
            'user_id': user_id,
            'exp': datetime.now(timezone.utc) + timedelta(seconds=3600)
        }
        invalid_token = jwt.encode(payload, 'wrong_secret_key', algorithm='HS256')

        # Verify should return None
        result = verify_jwt(invalid_token)
        assert result is None

    def test_verify_malformed_token_returns_none(self):
        """Test that verifying a malformed token returns None."""
        malformed_token = "this.is.not.a.valid.jwt"

        # Verify should return None
        result = verify_jwt(malformed_token)
        assert result is None

    def test_verify_empty_token_returns_none(self):
        """Test that verifying an empty token returns None."""
        # Verify should return None
        result = verify_jwt("")
        assert result is None

    def test_verify_none_token_returns_none(self):
        """Test that verifying None token returns None."""
        # Verify should return None
        result = verify_jwt(None)
        assert result is None

    def test_verify_token_with_missing_user_id_returns_none(self):
        """Test that token without user_id field returns None."""
        # Create a token without user_id
        payload = {
            'exp': datetime.now(timezone.utc) + timedelta(seconds=3600)
        }
        token_without_user_id = jwt.encode(payload, Config.JWT_SECRET, algorithm='HS256')

        # Verify should return None
        result = verify_jwt(token_without_user_id)
        assert result is None
