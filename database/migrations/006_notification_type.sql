-- Migration: Add Notification Type
-- Description: Adds notification_type column to notification_queue to distinguish filing vs IE notifications
-- Created: 2026-01-02

-- Add notification_type column
ALTER TABLE notification_queue
ADD COLUMN IF NOT EXISTS notification_type VARCHAR(20) DEFAULT 'filing';

-- Comment for documentation
COMMENT ON COLUMN notification_queue.notification_type
IS 'Type of notification: filing (campaign financial report) or ie (independent expenditure)';

-- Index for filtering by type
CREATE INDEX IF NOT EXISTS idx_queue_type ON notification_queue(notification_type);

-- Update unique constraint to include notification_type (prevents duplicates per type)
-- First drop the old constraint if it exists
ALTER TABLE notification_queue
DROP CONSTRAINT IF EXISTS notification_queue_user_id_candidate_id_filing_date_key;

-- Add new unique constraint including notification_type
ALTER TABLE notification_queue
ADD CONSTRAINT notification_queue_user_candidate_date_type_key
UNIQUE (user_id, candidate_id, filing_date, notification_type);
