import time
import os
import uuid
import yt_dlp
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
STORAGE_BUCKET = "video"

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def process_info(job):
    job_id = job['id']
    url = job['url']
    print(f"🔍 Fetching Metadata for Job {job_id}: {url}")
    
    ydl_opts = {
        'no_playlist': True,
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
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
            
            supabase.table("downloads_queue").update({
                "status": "awaiting_format", 
                "video_metadata": metadata,
                "updated_at": "now()"
            }).eq("id", job_id).execute()
            print(f"✅ Metadata Ready for Job {job_id}")
            
    except Exception as e:
        print(f"❌ Metadata Fetch Failed for {job_id}: {str(e)}")
        supabase.table("downloads_queue").update({
            "status": "failed",
            "error_message": f"Metadata Error: {str(e)}",
            "updated_at": "now()"
        }).eq("id", job_id).execute()

def process_download(job):
    job_id = job['id']
    url = job['url']
    format_id = job.get('format_id')
    
    print(f"🚀 Downloading Job {job_id} [Format: {format_id}]")
    
    # Update status to processing
    supabase.table("downloads_queue").update({"status": "processing"}).eq("id", job_id).execute()
    
    local_filename = f"{uuid.uuid4()}.mp4"
    storage_path = f"downloads/{local_filename}"
    
    ydl_opts = {
        'format': format_id if format_id else 'best',
        'outtmpl': local_filename,
        'no_playlist': True,
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        print(f"📦 Uploading to Supabase Storage...")
        with open(local_filename, 'rb') as f:
            supabase.storage.from_(STORAGE_BUCKET).upload(
                path=storage_path,
                file=f,
                file_options={"content-type": "video/mp4"}
            )
            
        public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(storage_path)
        
        supabase.table("downloads_queue").update({
            "status": "done",
            "result_url": public_url,
            "updated_at": "now()"
        }).eq("id", job_id).execute()
        
        print(f"✅ Download Finished! {public_url}")
        
    except Exception as e:
        print(f"❌ Download Failed for {job_id}: {str(e)}")
        supabase.table("downloads_queue").update({
            "status": "failed",
            "error_message": f"Download Error: {str(e)}",
            "updated_at": "now()"
        }).eq("id", job_id).execute()
        
    finally:
        if os.path.exists(local_filename):
            os.remove(local_filename)

def main():
    print("📡 Worker Active. Monitoring Supabase Queue (Local IP Mode)...")
    while True:
        try:
            # Check for generic pending download (original mode) or pending_info (new mode)
            # 1. First priority: metadata requests
            info_job = supabase.table("downloads_queue").select("*").eq("status", "pending_info").order("created_at").limit(1).execute()
            if info_job.data:
                process_info(info_job.data[0])
                continue

            # 2. Second priority: download requests
            download_job = supabase.table("downloads_queue").select("*").eq("status", "pending_download").order("created_at").limit(1).execute()
            if download_job.data:
                process_download(download_job.data[0])
                continue

            time.sleep(2)
        except Exception as e:
            print(f"⚠️ Polling Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
