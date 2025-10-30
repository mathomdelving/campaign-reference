-- Migration: User Candidate Follows
-- Description: Creates user_candidate_follows table for tracking which candidates users are following
-- Created: 2025-10-29

-- Create user_candidate_follows table
CREATE TABLE IF NOT EXISTS user_candidate_follows (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  candidate_id TEXT NOT NULL,

  -- Cached candidate info for display (denormalized for performance)
  candidate_name TEXT NOT NULL,
  party TEXT,
  office TEXT NOT NULL,  -- 'H' or 'S'
  state TEXT NOT NULL,
  district TEXT,

  -- Notification preferences
  notification_enabled BOOLEAN DEFAULT TRUE,

  -- Metadata
  followed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_notification_sent TIMESTAMP WITH TIME ZONE,

  -- Constraints: One follow per user per candidate
  UNIQUE(user_id, candidate_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_follows_user ON user_candidate_follows(user_id);
CREATE INDEX IF NOT EXISTS idx_follows_candidate ON user_candidate_follows(candidate_id);
CREATE INDEX IF NOT EXISTS idx_follows_notifications ON user_candidate_follows(user_id, notification_enabled);

-- Enable Row Level Security
ALTER TABLE user_candidate_follows ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can only access their own follows
CREATE POLICY "Users can view own follows"
  ON user_candidate_follows FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own follows"
  ON user_candidate_follows FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own follows"
  ON user_candidate_follows FOR DELETE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can update own follows"
  ON user_candidate_follows FOR UPDATE
  USING (auth.uid() = user_id);

-- Comments for documentation
COMMENT ON TABLE user_candidate_follows IS 'Tracks which candidates each user is following for notifications';
COMMENT ON COLUMN user_candidate_follows.candidate_id IS 'FEC candidate ID (e.g., H6AZ01234)';
COMMENT ON COLUMN user_candidate_follows.candidate_name IS 'Cached candidate name for quick display';
COMMENT ON COLUMN user_candidate_follows.notification_enabled IS 'Whether user wants email notifications for this candidate';
COMMENT ON COLUMN user_candidate_follows.last_notification_sent IS 'Timestamp of most recent notification sent to user about this candidate';
