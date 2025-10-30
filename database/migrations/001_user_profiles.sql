-- Migration: User Profiles
-- Description: Creates user_profiles table for extended user information
-- Created: 2025-10-29

-- Create user_profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name TEXT,
  organization TEXT,
  role TEXT, -- journalist, operative, researcher, enthusiast
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can only view and update their own profile
CREATE POLICY "Users can view own profile"
  ON user_profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
  ON user_profiles FOR INSERT
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON user_profiles FOR UPDATE
  USING (auth.uid() = id);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_profiles_id ON user_profiles(id);

-- Comments for documentation
COMMENT ON TABLE user_profiles IS 'Extended user profile information linked to Supabase Auth users';
COMMENT ON COLUMN user_profiles.display_name IS 'User''s preferred display name';
COMMENT ON COLUMN user_profiles.organization IS 'User''s organization (e.g., news outlet, campaign)';
COMMENT ON COLUMN user_profiles.role IS 'User type: journalist, operative, researcher, or enthusiast';
COMMENT ON COLUMN user_profiles.last_active IS 'Last time user logged in or performed an action';
