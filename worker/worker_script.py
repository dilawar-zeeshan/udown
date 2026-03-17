import os
import uuid
import datetime
import yt_dlp
import subprocess
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
            if progress % 10 == 0:
                supabase.table("downloads_queue").update({"progress": progress}).eq("id", JOB_ID).execute()
        except:
            pass

def expand_url(url):
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0].split("&")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    return url

def get_base_opts():
    """Base options that prioritize signature solving and stealth."""
    opts = {
        'no_playlist': True,
        'quiet': False,
        'no_warnings': False,
        # Explicitly point to node for signature solving
        'javascript_executable': 'node',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
        'nocheckcertificate': True,
    }
    if YOUTUBE_COOKIES:
        with open("cookies.txt", "w") as f:
            f.write(YOUTUBE_COOKIES)
        opts['cookiefile'] = "cookies.txt"
    return opts

def run_extraction_attempt(clients, use_cookies=True):
    """Tries a specific set of clients with/without cookies."""
    target_url = expand_url(URL)
    opts = get_base_opts()
    if not use_cookies:
        opts.pop('cookiefile', None)
    
    opts['extractor_args'] = {
        'youtube': {
            'player_client': clients,
            'include_dash_manifest': True,
            'include_hls_manifest': True,
            'player_skip': ['configs'] # Skip configs but NOT webpage to avoid PO Token blocks
        }
    }
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(target_url, download=False)

def get_metadata():
    print(f"🔍 [METADATA] Starting Nuclear Bypass Discovery for {URL}")
    
    # Verify Node for the logs
    try:
        node_v = subprocess.check_output(["node", "--version"]).decode().strip()
        print(f"DEBUG: Node confirmed at: {node_v}")
    except:
        print("CRITICAL: Node.js is MISSING. Signatures will fail.")

    strategies = [
        # Strategy A: TV client (No Cookies) - Often bypasses PO Token perfectly
        {"name": "TV Public", "clients": ["tv"], "cookies": False},
        # Strategy B: Android client (No Cookies) - Good fallback for music
        {"name": "Android Public", "clients": ["android"], "cookies": False},
        # Strategy C: Web Embedded (With Cookies) - Use user identity
        {"name": "Web Embedded Private", "clients": ["web_embedded"], "cookies": True},
        # Strategy D: IOS client (With Cookies) - High-level trust
        {"name": "IOS Private", "clients": ["ios"], "cookies": True},
        # Strategy E: Full Web (Absolute Fallback)
        {"name": "Full Web Fallback", "clients": ["web"], "cookies": True}
    ]

    last_error = "Unknown Error"
    for strategy in strategies:
        try:
            print(f"🛠️ Trying Strategy: {strategy['name']}...")
            info = run_extraction_attempt(strategy['clients'], strategy['cookies'])
            
            # Process success
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
                print(f"⚠️ Strategy {strategy['name']} returned no formats. Skipping...")
                continue
                
            update_job("awaiting_format", {"video_metadata": metadata})
            print(f"✅ SUCCESS using {strategy['name']}! Metadata uploaded.")
            return
        except Exception as e:
            last_error = str(e)
            print(f"❌ Strategy {strategy['name']} failed: {e}")

    update_job("failed", {"error_message": f"Global Block: {last_error}"})
    print("💀 All Nuclear Strategies Exhausted.")

def run_download():
    # Same staged approach for the actual download
    print(f"🚀 [DOWNLOAD] Starting Stage Download for {URL}...")
    update_job("processing")
    
    target_url = expand_url(URL)
    local_filename = f"{uuid.uuid4()}.mp4"
    storage_path = f"temp/{SESSION_ID}/{JOB_ID}.mp4"
    
    strategies = [
        {"clients": ["tv"], "cookies": False},
        {"clients": ["android"], "cookies": False},
        {"clients": ["web_embedded"], "cookies": True},
        {"clients": ["ios"], "cookies": True}
    ]

    for strategy in strategies:
        try:
            print(f"🛠️ Attempting download with {strategy['clients']} (Cookies: {strategy['cookies']})...")
            opts = get_base_opts()
            if not strategy['cookies']: opts.pop('cookiefile', None)
            
            opts.update({
                'format': FORMAT_ID if FORMAT_ID else 'best',
                'outtmpl': local_filename,
                'progress_hooks': [progress_hook],
                'extractor_args': {
                    'youtube': {
                        'player_client': strategy['clients'],
                        'include_dash_manifest': True,
                        'include_hls_manifest': True
                    }
                }
            })
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([target_url])
            
            # Successful download upload
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
            print(f"❌ Download attempt failed: {str(e)[:100]}")
            if os.path.exists(local_filename): os.remove(local_filename)

    raise Exception("Download failed across all clients.")

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
        if os.path.exists("cookies.txt"): os.remove("cookies.txt")

if __name__ == "__main__":
    main()
