-- Migration: Notification Queue
-- Description: Creates notification_queue table for tracking email notifications to send
-- Created: 2025-10-29

-- Create notification_queue table
CREATE TABLE IF NOT EXISTS notification_queue (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- Who and what
  user_id UUID NOT NULL,
  candidate_id TEXT NOT NULL,
  filing_date DATE NOT NULL,

  -- Snapshot of filing data (denormalized for email content)
  filing_data JSONB NOT NULL,

  -- Status tracking
  status TEXT DEFAULT 'pending', -- pending, sent, failed
  queued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  sent_at TIMESTAMP WITH TIME ZONE,
  error_message TEXT,
  retry_count INT DEFAULT 0,

  -- Prevent duplicate notifications
  UNIQUE(user_id, candidate_id, filing_date)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_queue_status ON notification_queue(status);
CREATE INDEX IF NOT EXISTS idx_queue_user ON notification_queue(user_id);
CREATE INDEX IF NOT EXISTS idx_queue_date ON notification_queue(queued_at);

-- Index for cleanup of old notifications (after 30 days)
CREATE INDEX IF NOT EXISTS idx_queue_cleanup ON notification_queue(sent_at) WHERE sent_at IS NOT NULL;

-- Comments for documentation
COMMENT ON TABLE notification_queue IS 'Queue of email notifications to send to users about new candidate filings';
COMMENT ON COLUMN notification_queue.user_id IS 'User to notify (references auth.users.id)';
COMMENT ON COLUMN notification_queue.candidate_id IS 'FEC candidate ID that filed a new report';
COMMENT ON COLUMN notification_queue.filing_date IS 'Date of the filing (used for deduplication)';
COMMENT ON COLUMN notification_queue.filing_data IS 'Snapshot of financial data to include in email (candidate name, amounts, etc.)';
COMMENT ON COLUMN notification_queue.status IS 'Current status: pending (not yet sent), sent (successfully delivered), failed (permanently failed after retries)';
COMMENT ON COLUMN notification_queue.retry_count IS 'Number of times we have attempted to send this notification';
