# External Integrations

- **Supabase**: Used for authentication (anon keys), database (job queue `downloads_queue`), and object storage (`video` bucket).
- **yt-dlp**: Core extraction engine for downloading videos from platforms like YouTube, Instagram, Facebook, and TikTok.
- **GitHub Actions**: mentioned as part of the execution strategy (`video_worker.yml`) for running workers headlessly.
