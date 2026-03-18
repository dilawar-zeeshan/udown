# Directory Layout

- `frontend/` - React SPA (Vite, Tailwind).
  - `src/App.jsx` - Main UI component.
  - `src/api.js` - API interactions and queue polling mechanism.
- `downloader-worker/` - Python worker scripts for processing jobs from the queue.
  - `worker.py` - Polling script that executes `yt-dlp`.
- `downloader-service/` - (Potentially legacy) FastAPI backend service.
- `supabase/` - DB definitions and Edge Functions.
  - `functions/` - Deno Edge Functions (e.g., `video-info`, `serve-video`, `download-proxy`).
  - `migrations/` - SQL patches.
- `.github/workflows/` - CI/CD and serverless worker configurations (e.g., `video_worker.yml`).
