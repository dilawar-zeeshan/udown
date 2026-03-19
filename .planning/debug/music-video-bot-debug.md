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

#### Hypothesis 4: JS Runtime Detection Failure -> CONFIRMED
- `yt-dlp` reports `JS runtimes: none` despite `node` being present in `/opt/hostedtoolcache/...`.
- `yt_dlp_ejs` is installed but lacks a handler to solve signatures.
- Without signature solving, YouTube blocks all video formats, returning only images/thumbnails.

### 6. Actions Taken
- Fixed `shutil` import.
- Added absolute path discovery for `node`.
- Removed broken `GetPOT` plugin.
- Added `yt-dlp-ejs` (needs JS runtime to work).

### 7. Resolution (In Progress)
🎯 **The worker is effectively blind to video formats because it cannot solve the JavaScript signature challenges.** We need to find a way to make `yt-dlp` see the `node` runtime or use a client that doesn't require complex signatures.

---
*Created: 2026-03-19*
