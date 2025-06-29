import re
from urllib.parse import urlparse, parse_qs, urlunparse

def clean_url(url):
    p = urlparse(url)
    q = parse_qs(p.query)
    q.pop('list', None)
    return urlunparse(p._replace(query="&".join(f"{k}={v[0]}" for k, v in q.items())))

def is_valid_url(u):
    patterns = [
        # YouTube
        r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]{11}',
        r'^(https?://)?(www\.)?(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)[\w-]{11}',
        r'^(https?://)?(www\.)?youtube\.com/playlist\?list=[\w-]+',
        # Facebook
        r'^(https?://)?(www\.)?facebook\.com/.+/videos/\d+',
        r'^(https?://)?(www\.)?facebook\.com/share/v/[\w-]+/?$',
        r'^(https?://)?(www\.)?facebook\.com/watch\?v=\d+',
        r'^(https?://)?(www\.)?facebook\.com/reel/\d+',
        r'^(https?://)?(www\.)?facebook\.com/share/v/[\w-]+',
        # Instagram
        r'^(https?://)?(www\.)?instagram\.com/reel/[\w-]+/?(\?.*)?$',
        r'^(https?://)?(www\.)?instagram\.com/reels?/[\w-]+/?(\?.*)?$',
        #  X
        r'^(https?://)?(www\.)?(x\.com|twitter\.com)/[\w-]+/status/\d+/?$',
        

    ]
    return any(re.match(p, u) for p in patterns)

def is_youtube(url):
    return 'youtube.com' in url or 'youtu.be' in url

def get_video_info(url):
    import yt_dlp
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        return ydl.extract_info(url, download=False)