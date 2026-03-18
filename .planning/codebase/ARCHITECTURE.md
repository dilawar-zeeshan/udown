# System Architecture

## Core Pattern: Asynchronous Job Queue
1. **Client** requests video info or download via **Supabase Edge Functions**.
2. **Edge Function** creates a record in the `downloads_queue` table with status `pending_info` or `pending_download`.
3. **Python Worker** polls the `downloads_queue` table continuously.
4. **Worker** picks up the job, processes it using `yt-dlp`, and uploads the result to **Supabase Storage**.
5. **Worker** updates the job record with `done` status and the `result_url`.
6. **Client** (React frontend) polls the Supabase REST endpoint until the job status becomes `done`, then serves the video to the user.

## Alternative/Legacy Service
There is also a `downloader-service` built with FastAPI that exposes synchronous endpoints (`/video-info` and `/prepare-download`). It appears the system has transitioned to or is experimenting with the serverless worker pattern instead.
