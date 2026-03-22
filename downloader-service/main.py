from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import yt_dlp
import os
import uuid
import shutil
from supabase import create_client, Client
from dotenv import load_dotenv

from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase configuration (Must be set in VM environment variables)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
STORAGE_BUCKET = "video"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class DownloadRequest(BaseModel):
    url: str

def cleanup_file(filepath: str):
    """Removes the local file after upload"""
    if os.path.exists(filepath):
        os.remove(filepath)

@app.get("/")
def health_check():
    return {"status": "active", "proxy": "FastAPI + Supabase Storage"}

@app.post("/video-info")
def get_info(request: DownloadRequest):
    ydl_opts = {
        'no_playlist': True,
        'quiet': True,
        'no_warnings': True,
        # Stealth args for YouTube
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
        'extractor_args': 'youtube:player_client=ios,web_embedded',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            formats = [
                {
                    "format_id": f.get("format_id"),
                    "quality": f.get("format_note") or f.get("resolution"),
                    "ext": f.get("ext"),
                    "filesize": f.get("filesize") or f.get("filesize_approx")
                }
                for f in info.get("formats", [])
                if f.get("vcodec") != "none" and (f.get("ext") == "mp4" or f.get("container") == "mp4")
            ]
            return {
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "formats": formats
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/prepare-download")
async def prepare_download(url: str, format_id: str, background_tasks: BackgroundTasks):
    """
    Downloads the video locally, uploads to Supabase Storage, and returns the URL.
    """
    file_id = str(uuid.uuid4())
    local_filename = f"{file_id}.mp4"
    storage_path = f"downloads/{local_filename}"

    ydl_opts = {
        'format': f"{format_id}+bestaudio/best" if format_id else "best",
        'merge_output_format': 'mp4',
        'outtmpl': local_filename,
        'no_playlist': True,
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
        'extractor_args': 'youtube:player_client=ios,web_embedded',
    }

    try:
        # 1. Download locally
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # 2. Upload to Supabase Storage
        with open(local_filename, 'rb') as f:
            supabase.storage.from_(STORAGE_BUCKET).upload(
                path=storage_path,
                file=f,
                file_options={"content-type": "video/mp4"}
            )

        # 3. Get Public URL
        public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(storage_path)

        # 4. Schedule local cleanup
        background_tasks.add_task(cleanup_file, local_filename)

        return {"download_url": public_url}

    except Exception as e:
        if os.path.exists(local_filename):
            os.remove(local_filename)
        raise HTTPException(status_code=500, detail=str(e))
