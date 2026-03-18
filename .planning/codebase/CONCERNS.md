# Codebase Concerns & Tech Debt

- **Polling Overhead**: The Python worker constantly polls Supabase every 2-5 seconds. This uses DB resources inefficiently compared to webhooks/Realtime subscriptions.
- **Frontend Polling**: The React app polls the REST API for job completion instead of using Supabase Realtime (WebSockets).
- **Multiple Backend Paradigms**: Both a Supabase queue-based worker system AND a FastAPI service exist. One should probably be formally deprecated.
- **Concurrent Workers**: The worker selection (`limit(1)`) does not explicitly lock rows (`FOR UPDATE SKIP LOCKED`), meaning multiple workers might pick up the same job if scaled horizontally.
- **yt-dlp Blocking**: `yt-dlp` operations are blocking the single worker thread. Long downloads might delay metadata fetching for other users.
