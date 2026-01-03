-- Migration: Add IE Notification Toggle
-- Description: Adds ie_notification_enabled column to user_candidate_follows
-- Created: 2026-01-02

-- Add IE notification toggle to user_candidate_follows
ALTER TABLE user_candidate_follows
ADD COLUMN IF NOT EXISTS ie_notification_enabled BOOLEAN DEFAULT TRUE;

-- Comment for documentation
COMMENT ON COLUMN user_candidate_follows.ie_notification_enabled
IS 'Whether user wants email notifications for independent expenditures targeting this candidate';

-- Index for efficient IE notification queries
CREATE INDEX IF NOT EXISTS idx_follows_ie_notifications
ON user_candidate_follows(user_id, ie_notification_enabled);
