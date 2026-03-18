# Project Roadmap

**3 phases** | **7 requirements mapped** | All v1 requirements covered ✓

| # | Phase | Goal | Requirements | Criteria |
|---|-------|------|--------------|------------------|
| 1 | Infrastructure reliability | Robust worker extraction mechanism | DL-01, DL-02, DL-03 | 3 |
| 2 | End-to-End Download Delivery | Store files and serve link to user | DL-04, DL-05, DEL-01 | 3 |
| 3 | Access Control | Basic session usage tracking | AUTH-01 | 2 |

---

## Phase Details

**Phase 1: Infrastructure reliability**
Goal: Ensure the worker is robust, handles metadata gracefully, and successfully serves to the frontend.
Requirements: DL-01, DL-02, DL-03
Success criteria:
1. Video metadata can be reliably extracted from Youtube and TikTok.
2. Background workers process metadata without hanging.
3. Formats correctly display on the Vite frontend.

**Phase 2: End-to-End Download Delivery**
Goal: Finalize download process and Cloud storage upload.
Requirements: DL-04, DL-05, DEL-01
Success criteria:
1. Videos successfully download and payload upload to Supabase Storage.
2. Direct download URL route correctly proxies/redirects the user to the file.
3. UI updates in real-time as the download proceeds.

**Phase 3: Access Control**
Goal: Track requests and implement anti-abuse session tracking.
Requirements: AUTH-01
Success criteria:
1. Anonymous session token tracks user requests.
2. UI retains local session memory for tracking.
