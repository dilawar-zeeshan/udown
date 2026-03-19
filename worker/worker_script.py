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
    
    # Strip playlist parameters for YouTube
    if "youtube.com/watch" in url:
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        u = urlparse(url)
        query = parse_qs(u.query)
        # Keep only 'v' parameter
        new_query = {}
        if 'v' in query:
            new_query['v'] = query['v']
        u = u._replace(query=urlencode(new_query, doseq=True))
        return urlunparse(u)
        
    return url

def get_base_opts():
    """Options optimized for POT providers and signature solving."""
    opts = {
        'no_playlist': True,
        'quiet': False,
        'verbose': True, # Enable verbose for deep GitHub Actions debugging
        'javascript_executable': 'node',
        'nocheckcertificate': True,
        # Enable the POT providers
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web_embedded'],
                'include_dash_manifest': True,
                'include_hls_manifest': True
            }
        }
    }
    if YOUTUBE_COOKIES and len(YOUTUBE_COOKIES.strip()) > 10:
        print(f"DEBUG: Found YOUTUBE_COOKIES secret (Length: {len(YOUTUBE_COOKIES)})")
        try:
            with open("cookies.txt", "w", encoding='utf-8') as f:
                f.write(YOUTUBE_COOKIES)
            opts['cookiefile'] = "cookies.txt"
            print("DEBUG: cookies.txt written successfully.")
        except Exception as e:
            print(f"ERROR Writing cookies: {e}")
    else:
        print("DEBUG: No YOUTUBE_COOKIES secret found or too short.")
    return opts

def get_metadata():
    print(f"🔍 [METADATA] POT-Enabled Discovery for {URL}")
    target_url = expand_url(URL)
    
    # Verify Node for the logs
    try:
        node_v = subprocess.check_output(["node", "--version"]).decode().strip()
        print(f"DEBUG: Node Version: {node_v}")
    except:
        print("CRITICAL: Node.js MISSING.")

    try:
        opts = get_base_opts()
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(target_url, download=False)
            
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
                raise Exception("POT Provider failed to unblock video formats.")
                
            update_job("awaiting_format", {"video_metadata": metadata})
            print(f"✅ SUCCESS! Metadata uploaded with POT protection.")
    except Exception as e:
        print(f"❌ POT Extraction failed: {e}")
        update_job("failed", {"error_message": f"POT Block: {str(e)}"})

def run_download():
    print(f"🚀 [DOWNLOAD] Starting POT-Protected Download for {URL}...")
    update_job("processing")
    
    target_url = expand_url(URL)
    local_filename = f"{uuid.uuid4()}.mp4"
    storage_path = f"temp/{SESSION_ID}/{JOB_ID}.mp4"
    
    try:
        opts = get_base_opts()
        opts.update({
            'format': FORMAT_ID if FORMAT_ID else 'best',
            'outtmpl': local_filename,
            'progress_hooks': [progress_hook]
        })
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([target_url])
        
        print(f"📦 Uploading Final Video...")
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
    except Exception as e:
        print(f"❌ POT Download failed: {e}")
        update_job("failed", {"error_message": str(e)})
    finally:
        if os.path.exists(local_filename): os.remove(local_filename)
        if os.path.exists("cookies.txt"): os.remove("cookies.txt")

def main():
    if not JOB_ID or not URL: 
        print("CRITICAL: Missing JOB_ID or VIDEO_URL environment variables.")
        return
        
    try:
        print(f"--- STARTING WORKER [Job: {JOB_ID}] ---")
        if MODE == "info": 
            get_metadata()
        else: 
            run_download()
        print("--- WORKER FINISHED SUCCESSFULLY ---")
    except Exception as e:
        import traceback
        error_msg = f"Fatal Worker Crash: {str(e)}\n{traceback.format_exc()}"
        print(f"CRITICAL: {error_msg}")
        try:
            update_job("failed", {"error_message": error_msg})
        except:
            print("CRITICAL: Failed to update Supabase after crash.")
        exit(1) # Ensure GitHub Action reflects failure
    finally:
        if os.path.exists("cookies.txt"): 
            os.remove("cookies.txt")

if __name__ == "__main__": 
    main()
