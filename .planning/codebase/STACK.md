# Tech Stack

## Frontend
- **Framework**: React 18, Vite
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios

## Backend / Workers
- **Language**: Python 3.x for workers, TypeScript/Deno for Edge Functions
- **Framework (Worker)**: Raw Python scripts polling DB
- **Framework (Service)**: FastAPI (`downloader-service/main.py`)
- **Core Library**: `yt-dlp` for video extraction

## Database & Storage
- **Provider**: Supabase (PostgreSQL for queue, Storage for videos)
