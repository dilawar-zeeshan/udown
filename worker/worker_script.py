import os
import uuid
import datetime
import yt_dlp
import subprocess
import re
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

def expand_url(url):
    """Expands youtu.be URLs to full watch URLs."""
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0].split("&")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    return url

def get_best_ydl_opts(use_cookies=True, clients=None):
    """Returns the best ydl options for the current environment."""
    if clients is None:
        clients = ['tv', 'web_embedded', 'android']
    
    opts = {
        'no_playlist': True,
        'quiet': False,
        'no_warnings': False,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
        'extractor_args': {
            'youtube': {
                'player_client': clients,
                'include_dash_manifest': True,
                'include_hls_manifest': True
            }
        }
    }
    
    if use_cookies and YOUTUBE_COOKIES:
        cookie_file = "cookies.txt"
        with open(cookie_file, "w") as f:
            f.write(YOUTUBE_COOKIES)
        opts['cookiefile'] = cookie_file
        
    return opts

def get_metadata():
    target_url = expand_url(URL)
    print(f"🔍 Fetching info for {target_url}...")
    
    # Check Node.js for signature solving
    try:
        node_v = subprocess.check_output(["node", "--version"]).decode().strip()
        print(f"DEBUG: Node version: {node_v}")
    except:
        print("DEBUG: Node.js NOT FOUND. Signature solving will likely fail.")

    # Strategy 1: TV client WITHOUT cookies (often bypasses PO Token)
    print("DEBUG: Strategy 1 - TV/Android client (No Cookies)...")
    try:
        ydl_opts = get_best_ydl_opts(use_cookies=False, clients=['tv', 'android'])
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=False)
            process_info(info)
            return
    except Exception as e:
        print(f"DEBUG: Strategy 1 failed: {e}")

    # Strategy 2: Web client WITH cookies (Standard fallback)
    print("DEBUG: Strategy 2 - Web client (With Cookies)...")
    try:
        ydl_opts = get_best_ydl_opts(use_cookies=True, clients=['web', 'web_embedded'])
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=False)
            process_info(info)
            return
    except Exception as e:
        print(f"DEBUG: Strategy 2 failed: {e}")
        
    # Final Error
    raise Exception("All bypass strategies failed. YouTube is heavily restricting this video on GitHub.")

def process_info(info):
    metadata = {
        "title": info.get("title"),
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "formats": []
    }
    
    for f in info.get("formats", []):
        if f.get("vcodec") != "none":
            metadata["formats"].append({
                "format_id": f.get("format_id"),
                "quality": f.get("format_note") or f.get("resolution"),
                "ext": f.get("ext"),
                "filesize": f.get("filesize") or f.get("filesize_approx")
            })
    
    if not metadata["formats"]:
        raise Exception("No downloadable video formats found for this video.")
        
    update_job("awaiting_format", {"video_metadata": metadata})
    print(f"✅ Metadata uploaded. Found {len(metadata['formats'])} formats.")

def run_download():
    target_url = expand_url(URL)
    print(f"🚀 Downloading {target_url} [Format: {FORMAT_ID}]...")
    update_job("processing")
    
    cleanup_session_storage()
    
    local_filename = f"{uuid.uuid4()}.mp4"
    storage_path = f"temp/{SESSION_ID}/{JOB_ID}.mp4"
    
    # Use the client roulette even for download to ensure we get the stream
    strategies = [
        (False, ['tv', 'android']),
        (True, ['web', 'web_embedded'])
    ]
    
    last_error = None
    for use_cookies, clients in strategies:
        try:
            ydl_opts = get_best_ydl_opts(use_cookies=use_cookies, clients=clients)
            ydl_opts.update({
                'format': FORMAT_ID if FORMAT_ID else 'best',
                'outtmpl': local_filename,
                'progress_hooks': [progress_hook],
            })
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([target_url])
            
            # If we reach here, download was successful
            print(f"📦 Uploading to Supabase Storage...")
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
            return
        except Exception as e:
            last_error = e
            print(f"DEBUG: Download attempt failed: {e}")
            if os.path.exists(local_filename):
                os.remove(local_filename)
            if os.path.exists("cookies.txt"):
                os.remove("cookies.txt")

    raise last_error

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
    finally:
        if os.path.exists("cookies.txt"):
            os.remove("cookies.txt")

if __name__ == "__main__":
    main()
