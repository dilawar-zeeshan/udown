# v1 Requirements

### Authentication
- [ ] **AUTH-01**: User can download videos anonymously via a shared or generated session token.

### Downloading & Metadata
- [ ] **DL-01**: User can paste a video link and see the video title, duration, and thumbnail.
- [ ] **DL-02**: User can select a format (quality/extension) from the available extracted formats.
- [ ] **DL-03**: Backend background workers handle the YT-DLP extraction without blocking the main web server.
- [ ] **DL-04**: System uploads the downloaded video to Supabase Storage.
- [ ] **DL-05**: User interface receives progress updates during the download phase.

### Delivery
- [ ] **DEL-01**: Provide a secure streaming/download link to the final processed video file.

---

## v2 Requirements (Deferred)
- [ ] User accounts and historical download lists.
- [ ] Configurable default preferences for quality.
- [ ] API access keys for third-party consumers.

## Out of Scope
- [Live Stream Recording] — Extremely high infrastructure cost and beyond our MVP scope for immediate video file delivery.
- [Video Transcoding/Re-encoding] — We only serve the native formats extracted by yt-dlp to avoid CPU-heavy ffmpeg processing on the server.

---

## Traceability
*(To be populated by ROADMAP.md mappings)*
