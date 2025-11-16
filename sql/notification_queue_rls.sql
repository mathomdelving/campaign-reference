-- Row Level Security for notification_queue table
-- Prevents unauthorized access to the email notification queue

-- Enable RLS
ALTER TABLE notification_queue ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any
DROP POLICY IF EXISTS "Service role full access" ON notification_queue;

-- Service role (backend scripts) can do everything
CREATE POLICY "Service role full access" ON notification_queue
  FOR ALL
  USING (auth.role() = 'service_role');

-- No public access - all access must go through backend scripts
-- Users cannot see, create, update, or delete queue entries directly

-- Verify RLS is enabled
SELECT
  tablename,
  rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename = 'notification_queue';
