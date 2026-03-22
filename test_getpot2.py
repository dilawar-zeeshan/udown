import yt_dlp
opts = {
    'quiet': False,
    'verbose': True,
    'extractor_args': {
        'youtubepot-bgutilscript': {
            'script_path': '/home/zee/Desktop/downloader/pot-server/server/src/generate_once.ts'
        },
        'youtube': {
            'player_client': ['ios', 'android', 'web']
        }
    }
}
with yt_dlp.YoutubeDL(opts) as ydl:
    try:
        info = ydl.extract_info("https://www.youtube.com/watch?v=BwntXFBNfOA", download=False)
        print("Success, found formats:", len(info.get('formats', [])))
    except Exception as e:
        print("Failed:", e)
