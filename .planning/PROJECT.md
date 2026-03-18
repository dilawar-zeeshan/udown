# VDownloader

## What This Is

A premium cloud-based video downloader for social media (YouTube, Instagram, Facebook, TikTok). Users paste a video link in a React web app, our serverless background workers process the video using `yt-dlp`, and the extracted video is served back to the user via Supabase Storage.

## Core Value

Reliable, platform-agnostic video extraction delivered through a fast and frictionless UI. 

## Requirements

### Validated

- ✓ [Video Info Extraction] — Fetch metadata and available formats for a given URL via Edge Functions.
- ✓ [Asynchronous Downloading] — Queue download jobs in Supabase and process them via background Python workers.
- ✓ [Direct Download Delivery] — Serve processed videos securely back to the user via signed/public Supabase URLs.
- ✓ [Polling UI] — React frontend that polls job status and displays progress.

### Active

- [ ] [Support user authentication]
- [ ] [Add format/quality preferences per user]
- [ ] [Improve worker scaling mechanisms]

### Out of Scope

- [Live Stream Recording] — High infrastructure cost and not part of the core value.

## Context

The architecture revolves around a serverless worker pattern where Edge Functions enqueue jobs to a Supabase Postgres table (`downloads_queue`) and a Python `yt-dlp` worker continuously polls and processes these jobs. We need to watch out for database polling overhead and blocking operations in the single-threaded worker.

## Constraints

- **Tech Stack**: React/Vite (Frontend), Supabase (DB/Storage/Edge Functions), Python + `yt-dlp` (Workers).
- **Execution**: `yt-dlp` operations are blocking; workers need to scale effectively or handle timeouts gracefully.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Using Supabase Database Queue | Avoids spinning up a heavy Redis/Celery stack for initial implementation | — Pending |

---
*Last updated: 2026-03-18 after project initialization*
