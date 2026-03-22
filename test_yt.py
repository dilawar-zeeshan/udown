import yt_dlp
opts = {
    'quiet': False,
    'extractor_args': {
        'youtube': {
            'player_client': ['ios', 'android']
        }
    }
}
with yt_dlp.YoutubeDL(opts) as ydl:
    try:
        info = ydl.extract_info("https://www.youtube.com/watch?v=BwntXFBNfOA", download=False)
        print("Success:", info.get('title'))
    except Exception as e:
        print("Failed:", e)
