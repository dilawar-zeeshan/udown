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

#### Hypothesis 1: Sign-in Required (Music Videos) -> Confirmed Missing
Music videos on YouTube often require a signed-in state. While user added `YOUTUBE_COOKIES` to GitHub Secrets, `worker.py` is NOT configured to use them.

#### Hypothesis 2: Cookie Format/Path Issue
`YOUTUBE_COOKIES` secret needs to be written to a file for `yt-dlp` to consume via `cookiefile` option.

#### Hypothesis 3: Playlist URL complexity
The reproduction URL is a playlist link. `yt-dlp` might be attempting to extract the full list or is sensitive to the list parameters.

#### Hypothesis 3: Bot-detection bypassing needs update
Current `user_agent` or `extractor_args` might be outdated for 2025 YouTube/TikTok anti-bot measures.

---
*Created: 2026-03-19*
