-- Fix RLS Policies for Downloader Tables
-- 1. Enable RLS
ALTER TABLE downloads_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE downloads_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE rate_limits ENABLE ROW LEVEL SECURITY;

-- 2. Grant FULL access to service role (Edge Functions & GHA Worker)
CREATE POLICY "Service Role Full Access" ON downloads_queue FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service Role Full Access" ON downloads_log FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service Role Full Access" ON rate_limits FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 3. Grant SELECT access to anon (Vite Frontend needs to read progress)
CREATE POLICY "Public Read Queue" ON downloads_queue FOR SELECT TO anon USING (true);
