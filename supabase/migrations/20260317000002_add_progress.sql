-- Add progress column to downloads_queue to track real-time download status
ALTER TABLE downloads_queue ADD COLUMN IF NOT EXISTS progress INTEGER DEFAULT 0;
