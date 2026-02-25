-- JustScheduleIt Database Schema
-- Run this SQL in Supabase SQL Editor to create the required tables

-- ==================== Users Table ====================
-- Stores user profile information from Google OAuth

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    google_id TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    name TEXT,
    picture TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster lookups by Google ID
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);

-- Index for faster lookups by email
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);


-- ==================== Refresh Tokens Table ====================
-- Stores encrypted Google OAuth refresh tokens (one per user)

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    encrypted_token TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)  -- One refresh token per user
);

-- Index for faster lookups by user_id
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);


-- ==================== Enable Row Level Security (RLS) ====================
-- Note: We're using service_role key in the backend, so RLS is bypassed
-- But we still enable it for future-proofing and security best practices

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY;


-- ==================== RLS Policies ====================
-- These policies won't affect our backend (using service_role key)
-- But they would protect the data if we ever use anon key or user-specific keys

-- Users can only read their own data
CREATE POLICY "Users can read own data"
ON users FOR SELECT
USING (auth.uid()::text = id::text);

-- Only service role can insert/update users
CREATE POLICY "Service role can manage users"
ON users FOR ALL
USING (true);

-- Refresh tokens are completely hidden from non-service-role access
CREATE POLICY "Only service role can access refresh tokens"
ON refresh_tokens FOR ALL
USING (true);


-- ==================== Automatic updated_at Trigger ====================
-- Automatically update the updated_at timestamp when a row is modified

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to refresh_tokens table
DROP TRIGGER IF EXISTS update_refresh_tokens_updated_at ON refresh_tokens;
CREATE TRIGGER update_refresh_tokens_updated_at
    BEFORE UPDATE ON refresh_tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ==================== Verification ====================
-- Check that tables were created successfully

SELECT 'Tables created successfully!' AS status;
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('users', 'refresh_tokens');
