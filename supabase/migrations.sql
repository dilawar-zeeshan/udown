-- Create downloads_log table
CREATE TABLE IF NOT EXISTS downloads_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  url TEXT NOT NULL,
  platform TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  ip TEXT NOT NULL
);

-- Create rate_limits table
CREATE TABLE IF NOT EXISTS rate_limits (
  ip TEXT PRIMARY KEY,
  request_count INTEGER DEFAULT 0,
  last_request TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create downloads_queue table for worker architecture
CREATE TABLE IF NOT EXISTS downloads_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  url TEXT NOT NULL,
  format_id TEXT,
  session_id TEXT, -- Added for storage cleanup
  status TEXT DEFAULT 'pending_info',
  video_metadata JSONB,
  result_url TEXT,
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Realtime setup (Enable for downloads_queue)
ALTER PUBLICATION supabase_realtime ADD TABLE downloads_queue;
