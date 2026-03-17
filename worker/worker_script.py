import os
import uuid
import yt_dlp
from supabase import create_client, Client

# Configuration from Environment (GitHub Secrets/Inputs)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
JOB_ID = os.getenv("JOB_ID")
URL = os.getenv("VIDEO_URL")
MODE = os.getenv("MODE") # info or download
FORMAT_ID = os.getenv("FORMAT_ID")
STORAGE_BUCKET = "video"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def update_job(status, data=None):
    payload = {"status": status, "updated_at": "now()"}
    if data:
        payload.update(data)
    supabase.table("downloads_queue").update(payload).eq("id", JOB_ID).execute()

def get_metadata():
    print(f"🔍 Fetching info for {URL}...")
    ydl_opts = {
        'no_playlist': True,
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(URL, download=False)
        metadata = {
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "formats": [
                {
                    "format_id": f.get("format_id"),
                    "quality": f.get("format_note") or f.get("resolution"),
                    "ext": f.get("ext"),
                    "filesize": f.get("filesize") or f.get("filesize_approx")
                }
                for f in info.get("formats", [])
                if f.get("vcodec") != "none" and (f.get("ext") == "mp4" or f.get("container") == "mp4")
            ]
        }
        update_job("awaiting_format", {"video_metadata": metadata})
        print("✅ Metadata uploaded to Supabase.")

def run_download():
    print(f"🚀 Downloading {URL} [Format: {FORMAT_ID}]...")
    update_job("processing")
    
    local_filename = f"{uuid.uuid4()}.mp4"
    storage_path = f"downloads/{local_filename}"
    
    ydl_opts = {
        'format': FORMAT_ID if FORMAT_ID else 'best',
        'outtmpl': local_filename,
        'no_playlist': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([URL])
            
        print(f"📦 Uploading to Supabase Storage...")
        with open(local_filename, 'rb') as f:
            supabase.storage.from_(STORAGE_BUCKET).upload(
                path=storage_path,
                file=f,
                file_options={"content-type": "video/mp4"}
            )
            
        public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(storage_path)
        update_job("done", {"result_url": public_url})
        print(f"✅ Download Finished! {public_url}")
        
    finally:
        if os.path.exists(local_filename):
            os.remove(local_filename)

def main():
    if not JOB_ID or not URL:
        print("❌ Missing JOB_ID or VIDEO_URL")
        return

    try:
        if MODE == "info":
            get_metadata()
        else:
            run_download()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        update_job("failed", {"error_message": str(e)})

if __name__ == "__main__":
    main()
