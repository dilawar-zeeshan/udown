import os
import uuid
import datetime
import yt_dlp
from supabase import create_client, Client

# Configuration from Environment (GitHub Secrets/Inputs)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
JOB_ID = os.getenv("JOB_ID")
URL = os.getenv("VIDEO_URL")
MODE = os.getenv("MODE") # info or download
FORMAT_ID = os.getenv("FORMAT_ID")
SESSION_ID = os.getenv("SESSION_ID") or "default"
YOUTUBE_COOKIES = os.getenv("YOUTUBE_COOKIES")
STORAGE_BUCKET = "video"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def cleanup_session_storage():
    """Deletes all files in the current session's folder to save space."""
    try:
        folder_path = f"temp/{SESSION_ID}"
        files = supabase.storage.from_(STORAGE_BUCKET).list(folder_path)
        if files:
            file_paths = [f"{folder_path}/{f['name']}" for f in files]
            supabase.storage.from_(STORAGE_BUCKET).remove(file_paths)
            print(f"🧹 Cleaned up {len(file_paths)} files from session {SESSION_ID}")
    except Exception as e:
        print(f"⚠️ Session cleanup failed (might be empty): {e}")

def update_job(status, data=None):
    payload = {
        "status": status, 
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    if data:
        payload.update(data)
    supabase.table("downloads_queue").update(payload).eq("id", JOB_ID).execute()

def progress_hook(d):
    if d['status'] == 'downloading':
        try:
            p = d.get('_percent_str', '0%').replace('%','')
            progress = int(float(p))
            # Update every 10% to avoid spamming the DB
            if progress % 10 == 0:
                supabase.table("downloads_queue").update({"progress": progress}).eq("id", JOB_ID).execute()
        except:
            pass

def get_metadata():
    print(f"🔍 Fetching info for {URL}...")
    ydl_opts = {
        'no_playlist': True,
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
        'extractor_args': {
            'youtube': {
                'player_client': ['tv_embedded', 'web_embedded'],
                'include_dash_manifest': True,
                'include_hls_manifest': True
            }
        }
    }
    
    print(f"DEBUG: YOUTUBE_COOKIES env length: {len(YOUTUBE_COOKIES) if YOUTUBE_COOKIES else 'MISSING'}")
    
    cookie_file = None
    if YOUTUBE_COOKIES:
        cookie_file = "cookies.txt"
        with open(cookie_file, "w") as f:
            f.write(YOUTUBE_COOKIES)
        ydl_opts['cookiefile'] = cookie_file
        print(f"DEBUG: Created cookie file: {cookie_file} (exists: {os.path.exists(cookie_file)})")

    try:
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
    finally:
        if cookie_file and os.path.exists(cookie_file):
            os.remove(cookie_file)

def run_download():
    print(f"🚀 Downloading {URL} [Format: {FORMAT_ID}]...")
    update_job("processing")
    
    # Pre-download cleanup to save space
    cleanup_session_storage()
    
    local_filename = f"{uuid.uuid4()}.mp4"
    storage_path = f"temp/{SESSION_ID}/{JOB_ID}.mp4"
    
    ydl_opts = {
        'format': FORMAT_ID if FORMAT_ID else 'best',
        'outtmpl': local_filename,
        'no_playlist': True,
        'progress_hooks': [progress_hook],
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
        'extractor_args': {
            'youtube': {
                'player_client': ['tv_embedded', 'web_embedded'],
                'include_dash_manifest': True,
                'include_hls_manifest': True
            }
        }
    }
    
    print(f"DEBUG: YOUTUBE_COOKIES env length: {len(YOUTUBE_COOKIES) if YOUTUBE_COOKIES else 'MISSING'}")

    cookie_file = None
    if YOUTUBE_COOKIES:
        cookie_file = "cookies_dl.txt"
        with open(cookie_file, "w") as f:
            f.write(YOUTUBE_COOKIES)
        ydl_opts['cookiefile'] = cookie_file
        print(f"DEBUG: Created cookie file: {cookie_file} (exists: {os.path.exists(cookie_file)})")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([URL])
            
        print(f"📦 Uploading to Supabase Storage...")
        # Mark as uploading
        supabase.table("downloads_queue").update({"status": "uploading", "progress": 100}).eq("id", JOB_ID).execute()
        
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
        if cookie_file and os.path.exists(cookie_file):
            os.remove(cookie_file)
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
