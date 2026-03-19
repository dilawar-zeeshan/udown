# Debug Session: Music Video & Bot Detection failures

**Status:** GATHERING SYMPTOMS
**Slug:** music-video-bot-debug
**Goal:** find_and_fix

## 🔍 Symptom Tracking

### 1. Expected Behavior
- Metadata extraction and download for music videos should follow the same pattern as other videos.
- Library should not be blocked/detected as bot when cookies are provided.

### 2. Actual Behavior
- Music videos fail (Exit code 1 in GitHub Actions).
- Library is detected as bot (User reports bot detection).
- [x] UI reports: "Polling timed out. The worker might be busy."
- [x] GitHub Actions: "Process completed with exit code 1."

### 3. Error Messages
- `Process completed with exit code 1` (GitHub Actions)
- `Polling timed out` (Frontend UI)

### 4. Reproduction URLs
- `https://www.youtube.com/watch?v=j18MRhEfmPk&list=RDj18MRhEfmPk&start_radio=1` (YouTube Music Video)

### 5. Investigation Log

#### Hypothesis 1: Sign-in Required (Music Videos) -> FIXED
- Logic to load `YOUTUBE_COOKIES` from environment and write to `cookies.txt` was verified and improved.

#### Hypothesis 2: Cookie Format/Path Issue -> FIXED
- Added UTF-8 encoding and existence checks for cookie writing.

#### Hypothesis 3: Playlist URL complexity -> FIXED
- Added URL cleaning logic to strip `&list=...` and other parameters from YouTube watch URLs.

### 6. Actions Taken
- Updated `worker/worker_script.py` with the above fixes.
- Added global exception handling to report tracebacks to Supabase/Logs.
- Enabled `verbose` mode for `yt-dlp`.
- Removed redundant `downloader-worker/worker.py`.

### 7. Resolution
🎯 **The worker was not properly stripping playlist parameters from music video URLs and lacked internal logic to consume the `YOUTUBE_COOKIES` secret provided in GitHub Actions.**

---
*Created: 2026-03-19*
