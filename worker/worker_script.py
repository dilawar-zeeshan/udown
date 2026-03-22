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
    try:
        payload = {
            "status": status, 
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        if data:
            payload.update(data)
        print(f"DEBUG: Updating job {JOB_ID} to {status}...")
        res = supabase.table("downloads_queue").update(payload).eq("id", JOB_ID).execute()
        print(f"DEBUG: Supabase update response: {res}")
    except Exception as e:
        print(f"ERROR: Failed to update Supabase: {e}")

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
                'player_client': ['tvhtml5', 'android'],
                'include_dash_manifest': True,
                'include_hls_manifest': True
            }
        },
        'noprogress': True,
        'no_color': True,
        'remote_components': {'ejs:github'},
    }
    
    
    if use_cookies and YOUTUBE_COOKIES and len(YOUTUBE_COOKIES.strip()) > 10:
        print(f"DEBUG: Found YOUTUBE_COOKIES secret (Length: {len(YOUTUBE_COOKIES)})")
        try:
            raw_cookies = YOUTUBE_COOKIES.strip()
            if "Netscape" not in raw_cookies and "\t" not in raw_cookies and "=" in raw_cookies:
                # Convert raw string to Netscape format
                import time
                expire = int(time.time()) + 31536000
                netscape_lines = ["# Netscape HTTP Cookie File\n"]
                for str_pair in raw_cookies.split(";"):
                    str_pair = str_pair.strip()
                    if not str_pair or "=" not in str_pair: continue
                    k, v = str_pair.split("=", 1)
                    prefix = "#HttpOnly_.youtube.com" if k.startswith("__Secure") else ".youtube.com"
                    netscape_lines.append(f"{prefix}\tTRUE\t/\tTRUE\t{expire}\t{k}\t{v}\n")
                with open("cookies.txt", "w", encoding="utf-8") as f:
                    f.writelines(netscape_lines)
                print("DEBUG: Converted raw cookies string to Netscape format.")
            else:
                with open("cookies.txt", "w", encoding='utf-8') as f:
                    f.write(raw_cookies)
                print("DEBUG: cookies.txt written successfully from Netscape format.")
            opts['cookiefile'] = "cookies.txt"
        except Exception as e:
            print(f"ERROR Writing cookies: {e}")
    else:
        print("DEBUG: No cookies injected (either missing or use_cookies=False).")

def get_metadata():
    print(f"🔍 [METADATA] POT-Enabled Discovery for {URL}")
    target_url = expand_url(URL)
    
    # Verify Deno for the logs
    try:
        print(f"DEBUG: Deno Version: {subprocess.check_output(['/home/runner/.deno/bin/deno', '--version']).decode().strip().splitlines()[0]}")
    except:
        print("DEBUG: Deno check failed in script.")

    try:
        # Verify Supabase connection
        print(f"DEBUG: Testing Supabase connection to {SUPABASE_URL}...")
        supabase.table("downloads_queue").select("id").limit(1).execute()
        print("DEBUG: Supabase connection HEALTHY.")
        
        info = None
        # Try 1: Best chance with prioritized clients and cookies
        try:
            print("DEBUG: Attempting metadata extraction with TV/Mobile clients...")
            opts = get_base_opts()
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(target_url, download=False)
        except Exception as e:
            print(f"DEBUG: Primary attempt failed: {e}")
            # Final attempt: no cookies, fallback clients
            print("DEBUG: Final fallback - Retry without cookies using iOS/Android clients...")
            import os
            if os.path.exists("cookies.txt"):
                os.remove("cookies.txt")
            
            opts = get_base_opts(use_cookies=False)
            opts['extractor_args']['youtube']['player_client'] = ['android', 'ios']
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(target_url, download=False)

        if not info or not info.get('formats'):
            print("DEBUG: No formats found in either attempt.")
            raise Exception("YouTube blocked all formats (Manifest Error)")

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
            raise Exception("No video formats available for this selection.")
            
        update_job("awaiting_format", {"video_metadata": metadata})
        print(f"✅ SUCCESS! Metadata extracted for: {metadata.get('title')}")

    except Exception as e:
        import traceback
        print(f"❌ Extraction failed: {e}")
        # Diagnostic: Try to list formats to see what YouTube is allowing
        try:
            print("🔍 [DIAGNOSTIC] Final attempt to list available formats...")
            opts = get_base_opts(use_cookies=False)
            opts['listformats'] = True
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.extract_info(target_url, download=False)
        except:
            pass
        
        update_job("failed", {"error_message": f"Download Blocked: {str(e)}"})
        raise e

def run_download():
    print(f"🚀 [DOWNLOAD] Starting POT-Protected Download for {URL}...")
    update_job("processing")
    
    target_url = expand_url(URL)
    local_filename = f"{uuid.uuid4()}.mp4"
    storage_path = f"temp/{SESSION_ID}/{JOB_ID}.mp4"
    
    try:
        opts = get_base_opts()
        opts.update({
            'format': f"{FORMAT_ID}+bestaudio/best" if FORMAT_ID else "best",
            'merge_output_format': 'mp4',
            'outtmpl': local_filename,
            'progress_hooks': [progress_hook]
        })
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([target_url])
        except Exception as retry_e:
            print(f"DEBUG: Primary download attempt failed: {retry_e}")
            print("DEBUG: Retrying download without cookies...")
            import os
            if os.path.exists("cookies.txt"):
                os.remove("cookies.txt")
            opts = get_base_opts(use_cookies=False)
            opts['extractor_args']['youtube']['player_client'] = ['android', 'ios']
            opts.update({
                'format': f"{FORMAT_ID}+bestaudio/best" if FORMAT_ID else "best",
                'merge_output_format': 'mp4',
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
