import os
import uuid
import datetime
import yt_dlp
import shutil
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

def get_base_opts(use_cookies=True):
    # Detailed PATH debug for GHA
    print(f"DEBUG: PATH: {os.environ.get('PATH')}")
    node_path = shutil.which('node')
    print(f"DEBUG: Found node at: {node_path}")
    
    # Verify node can actually run a script
    try:
        test_out = subprocess.check_output([node_path or 'node', '-e', 'console.log("HEALTHY")'], timeout=5).decode().strip()
        print(f"DEBUG: Node execution test: {test_out}")
    except Exception as e:
        print(f"DEBUG: Node execution test FAILED: {str(e)}")

    opts = {
        'no_playlist': True,
        'quiet': False,
        'verbose': True,
        'javascript_executable': '/home/runner/.deno/bin/deno',
        'nocheckcertificate': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['tvhtml5', 'android', 'ios', 'web_embedded'],
                'include_dash_manifest': True,
                'include_hls_manifest': True
            }
        },
        'noprogress': True,
        'no_color': True,
        'remote_components': {'ejs:github'},
    }
    
    # Configure GetPOT with local script if path found in workflow
    bgutil_script = os.getenv("BGUTIL_SCRIPT_PATH")
    if bgutil_script and os.path.exists(bgutil_script):
        print(f"DEBUG: Using local BGUTIL script at {bgutil_script}")
        if 'extractor_args' not in opts: opts['extractor_args'] = {}
        opts['extractor_args']['youtube+GetPOT'] = {
            'provider': 'bgutil:script-deno',
            'bgutil:script-deno': {
                'script_path': bgutil_script
            }
        }
    
    if use_cookies and YOUTUBE_COOKIES and len(YOUTUBE_COOKIES.strip()) > 10:
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
        # Try 1: Full options with cookies
        print("DEBUG: Attempt 1 - Full options with cookies...")
        opts = get_base_opts(use_cookies=True)
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(target_url, download=False)
    except Exception as e:
        print(f"DEBUG: Attempt 1 failed: {e}")
        try:
            # Try 2: No cookies, mobile clients (android/ios) are much better here
            print("DEBUG: Attempt 2 - No cookies, focusing on mobile clients...")
            opts = get_base_opts(use_cookies=False)
            opts['extractor_args']['youtube']['player_client'] = ['android', 'ios']
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(target_url, download=False)
        except Exception as e2:
            print(f"❌ All extraction attempts failed.")
            # Diagnostic: Try to list formats to see what YouTube is allowing
            try:
                print("🔍 [DIAGNOSTIC] Final attempt to list available formats...")
                opts = get_base_opts(use_cookies=False)
                opts['listformats'] = True
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.extract_info(target_url, download=False)
            except:
                pass
            
            update_job("failed", {"error_message": f"Download Blocked (Music Video restriction): {str(e2)}"})
            raise e2

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
        raise e  # Re-raise
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
