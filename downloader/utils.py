# [FILE NAME]: utils.py
# Utility functions for URL processing and video information
import re
from urllib.parse import urlparse, parse_qs, urlunparse
import yt_dlp  # YouTube download library

def clean_url(url):
    """
    Cleans YouTube URLs by removing playlist parameters.
    Prevents accidental playlist downloads when user wants single video.
    """
    # Break URL into components
    p = urlparse(url)
    # Parse query parameters
    q = parse_qs(p.query)
    # Remove 'list' parameter (playlist ID)
    q.pop('list', None)
    # Rebuild URL without playlist parameter
    return urlunparse(p._replace(query="&".join(f"{k}={v[0]}" for k, v in q.items())))

def is_valid_url(u):
    """
    Validates URLs against supported platforms and patterns.
    Returns True if URL matches known video platforms.
    """
    # List of regex patterns for supported platforms
    patterns = [
        # YouTube patterns
        r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]{11}',
        r'^(https?://)?(www\.)?(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)[\w-]{11}',
        r'^(https?://)?(www\.)?youtube\.com/playlist\?list=[\w-]+',
        # Facebook patterns
        r'^(https?://)?(www\.)?facebook\.com/.+/videos/\d+',
        r'^(https?://)?(www\.)?facebook\.com/share/v/[\w-]+/?$',
        r'^(https?://)?(www\.)?facebook\.com/watch\?v=\d+',
        r'^(https?://)?(www\.)?facebook\.com/reel/\d+',
        r'^(https?://)?(www\.)?facebook\.com/share/v/[\w-]+',
        # Instagram patterns
        r'^(https?://)?(www\.)?instagram\.com/reel/[\w-]+/?(\?.*)?$',
        r'^(https?://)?(www\.)?instagram\.com/reels?/[\w-]+/?(\?.*)?$',
        # Twitter/X patterns
        r'^(https?://)?(www\.)?(x\.com|twitter\.com)/[\w-]+/status/\d+/?$',
    ]
    # Check if URL matches any pattern
    return any(re.match(p, u) for p in patterns)

def is_youtube(url):
    """Checks if URL is from YouTube domain"""
    return 'youtube.com' in url or 'youtu.be' in url

def get_video_info(url, download_type='1'):
    """
    Fetches video/playlist information using yt_dlp library.
    download_type: '2' = playlist, '1' = single video
    """
    # Configure yt_dlp options
    ydl_opts = {
        'extract_flat': False,  # ✅ Force full extraction even for playlists
        'quiet': True,  # Suppress output
        'force_generic_extractor': False,  # Use platform-specific extractors
    }
    
    # Create YouTube DL instance
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Fetch video information without downloading
        info = ydl.extract_info(url, download=False)
        if not info:
            raise Exception("yt-dlp failed to extract info")        
        return info