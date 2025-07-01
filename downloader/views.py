# [FILE NAME]: views.py
# Handles user requests and download processing
from django.conf import settings
import shutil
from django.shortcuts import render, redirect
from django.http import FileResponse, HttpResponse
from .forms import DownloadForm
from .utils import clean_url, is_valid_url, is_youtube, get_video_info
import os
import yt_dlp
import tempfile
import time
import random
import logging
import zipfile
from django.utils.text import slugify
from pathlib import Path
from datetime import datetime


# testing 
import base64
from django.utils.text import slugify

def get_cookies_temp_file():
    """Handle cookies from environment variable with multiple fallback methods"""
    try:
        if hasattr(settings, 'YT_COOKIES_PATH') and os.path.exists(settings.YT_COOKIES_PATH):
            return settings.YT_COOKIES_PATH

        cookies_base64 = os.getenv("YT_COOKIES_BASE64")
        if cookies_base64:
            cookies_content = base64.b64decode(cookies_base64).decode('utf-8')
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as f:
                f.write(cookies_content)
                return f.name

        cookies_content = os.getenv("YT_COOKIES_CONTENT")
        if cookies_content:
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as f:
                f.write(cookies_content)
                return f.name

        return None
    except Exception as e:
        logger.error(f"Cookie handling error: {e}")
        return None

def rate_limited(max_per_minute=10):
    min_interval = 60.0 / float(max_per_minute)
    def decorator(f):
        last_time_called = [0.0]
        def wrapped(*args, **kwargs):
            elapsed = time.time() - last_time_called[0]
            wait_time = min_interval - elapsed
            if wait_time > 0:
                time.sleep(wait_time)
            last_time_called[0] = time.time()
            return f(*args, **kwargs)
        return wrapped
    return decorator






# Set up logging
logger = logging.getLogger(__name__)


# for debugg only
def print_with_timestamp(message):
    now = datetime.now()
    timestamp = now.strftime("[%d/%b/%Y %H:%M:%S]")  # Format like [01/Jul/2025 16:10:10]
    print(f"{timestamp} {message}")


def index(request):
    """
    Home view - handles the download form submission.
    Validates URL and stores session data for next steps.
    """
    if request.method == 'POST':
        form = DownloadForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            download_type = form.cleaned_data['download_type']
            
            # Validate URL format
            if not is_valid_url(url):
                form.add_error('url', 'Invalid URL')
                return render(request, 'downloader/index.html', {'form': form})
            
            # Clean YouTube URLs to remove playlist parameters
            if download_type == '1' and is_youtube(url):
                url = clean_url(url)
            
            # Store in session for next steps
            request.session['download_info'] = {
                'url': url,
                'download_type': download_type
            }
            
            # Redirect to preview page
            return redirect('downloader:preview')
    else:
        # Initial form display
        form = DownloadForm()
    
    return render(request, 'downloader/index.html', {'form': form})



def preview(request):
    """
    Displays preview information for a video or playlist.
    Shows available formats for single videos or
    the list of videos and resolutions for playlists,
    including total playlist size broken down by resolution.
    """

    # Step 1: Check if user came here properly by checking session data
    if not request.session.get('download_info'):
        print_with_timestamp("No download_info in session; redirecting to index.")
        return redirect('downloader:index')
    
    # Extract URL and download type (video or playlist) from session
    url = request.session['download_info']['url']
    download_type = request.session['download_info']['download_type']

    print_with_timestamp(f"Preview requested for URL: {url}")
    print_with_timestamp(f"Download type: {download_type}")

    # List of professional standard resolutions for rounding (144p to 8K)
    allowed_resolutions = [144, 240, 360, 480, 720, 1080, 1440, 2160, 4320]

    def nearest_resolution(res):
        """
        Helper function to round given resolution to nearest
        allowed professional resolution.
        """
        return min(allowed_resolutions, key=lambda x: abs(x - res))

    try:
        # Step 2: Fetch video or playlist info using your helper
        print_with_timestamp("Fetching video info using get_video_info()")
        info = get_video_info(url, download_type)
        print_with_timestamp("Video info fetched successfully")

        # Step 3: Handle playlist case
        if download_type == '2' and 'entries' in info:
            print_with_timestamp("Detected playlist with multiple entries")

            videos = []             # List of videos in the playlist
            all_resolutions = set() # Set to collect all unique resolutions
            total_sizes_per_res = {}  # Dict to store total size per resolution

            # Loop through each video entry in playlist
            for idx, entry in enumerate(info['entries']):
                if not entry:
                    print_with_timestamp(f"Skipping empty playlist entry at index {idx}")
                    continue  # Skip empty entries

                formats = entry.get('formats', [])
                
                # Extract all heights for video formats (ignore audio-only)
                heights = {f['height'] for f in formats if f.get('height') and f.get('vcodec') != 'none'}
                # Round these heights to nearest allowed resolutions
                rounded_heights = {nearest_resolution(h) for h in heights}
                # Update the global resolution set
                all_resolutions.update(rounded_heights)

                # Calculate max filesize per resolution for this video
                sizes_for_video = {}
                for f in formats:
                    if f.get('height') and f.get('vcodec') != 'none':
                        rounded_height = nearest_resolution(f['height'])
                        size = f.get('filesize') or f.get('filesize_approx') or 0
                        # Keep max size per resolution per video
                        if rounded_height not in sizes_for_video or size > sizes_for_video[rounded_height]:
                            sizes_for_video[rounded_height] = size
                
                # Add sizes of this video to total sizes per resolution
                for res, size in sizes_for_video.items():
                    total_sizes_per_res[res] = total_sizes_per_res.get(res, 0) + size

                # Add video basic info for template
                videos.append({
                    'title': entry.get('title', 'Untitled'),
                    'thumbnail': entry.get('thumbnail'),
                    'id': entry.get('id'),
                })

                print_with_timestamp(
                    f"Processed playlist video: '{entry.get('title', 'Untitled')}', "
                    f"size by resolution: {[f'{r}p={sizes_for_video[r]/(1024*1024):.2f}MB' for r in sizes_for_video]}"
                )

            # Sort resolutions descending
            sorted_resolutions = sorted(all_resolutions, reverse=True)

            # Prepare playlist formats list for template table with total size per resolution (in MB)
            playlist_formats = []
            for res in sorted_resolutions:
                size_mb = round(total_sizes_per_res.get(res, 0) / (1024 * 1024), 2)
                playlist_formats.append({
                    'height': res,
                    'ext': 'Various',
                    'filesize': size_mb,
                })

            print_with_timestamp(f"Total playlist size per resolution (MB): {playlist_formats}")

            context = {
                'type': 'playlist',
                'title': info.get('title', 'Untitled Playlist'),
                'thumbnail': info.get('thumbnail'),
                'videos': videos,
                'url': url,
                'formats': playlist_formats,
            }

        else:
            # Step 4: Single video case
            print_with_timestamp("Detected single video")

            formats = []
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none' and f.get('height'):
                    rounded_height = nearest_resolution(f['height'])
                    formats.append({
                        'height': rounded_height,
                        'ext': f['ext'],
                        'filesize': f.get('filesize') or f.get('filesize_approx', 0),
                    })

            # Remove duplicates by resolution and sort descending
            formats = sorted(
                {f['height']: f for f in formats}.values(),
                key=lambda x: x['height'],
                reverse=True
            )

            print_with_timestamp(f"Found {len(formats)} video formats with rounded resolutions")

            context = {
                'type': 'video',
                'title': info.get('title', 'Untitled Video'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration'),
                'formats': formats,
                'url': url,
            }

        print_with_timestamp("Rendering preview template with context")
        return render(request, 'downloader/preview.html', context)

    except Exception as e:
        print_with_timestamp(f"Exception in preview: {str(e)}")
        return render(request, 'downloader/index.html', {
            'form': DownloadForm(),
            'error': f'Error retrieving video info: {str(e)}'
        })

    


@rate_limited(max_per_minute=6) # testing to solve yt cookies problem
def download(request):
    """
    Handles the actual download process.
    Creates temporary directory, downloads content, and returns file response.
    """
    print_with_timestamp('Download started')

    if request.method != 'POST':
        print_with_timestamp('Request method not POST, redirecting to index')
        return redirect('downloader:index')

    if not request.session.get('download_info'):
        print_with_timestamp('No download_info in session, redirecting to index')
        return redirect('downloader:index')

    url = request.session['download_info']['url']
    download_type = request.session['download_info']['download_type']
    media_type = request.POST.get('media_type', 'video')
    resolution = request.POST.get('resolution')

    print_with_timestamp(f'URL: {url}')
    print_with_timestamp(f'Download type: {download_type}')
    print_with_timestamp(f'Media type: {media_type}')
    print_with_timestamp(f'Resolution: {resolution}')

    temp_dir = tempfile.mkdtemp()
    print_with_timestamp(f'Temporary directory created at: {temp_dir}')

    # Progress hook for yt-dlp to print download status
    """ def progress_hook(d):
        if d['status'] == 'downloading':
            print_with_timestamp(f"Downloading: {d.get('filename', '')} {d.get('_percent_str', '')}")
        elif d['status'] == 'finished':
            print_with_timestamp(f"Finished downloading {d.get('filename', '')}") """

    try:
        print_with_timestamp('Configuring yt-dlp options...')
        ydl_opts = {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.youtube.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            'geo_bypass': True,
            'force_ipv4': True,
            'quiet': True,
            'no_warnings': True,
            # 'cookies': settings.YT_COOKIES_PATH,
            'cookiefile': get_cookies_temp_file(),
            'cachedir': False,
            'no_cache_dir': True,
            # 'progress_hooks': [progress_hook],
        }

        postprocessors = []
        if media_type == 'video':
            postprocessors.append({
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            })
            print_with_timestamp('Configured for video post-processing (mp4)')
        else:
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            })
            print_with_timestamp('Configured for audio extraction (mp3)')
        ydl_opts['postprocessors'] = postprocessors

        print_with_timestamp('Extracting video information without downloading...')
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        print_with_timestamp('Video information extracted successfully')

        if 'entries' in info:
            print_with_timestamp('Detected playlist')
            ydl_opts['outtmpl'] = os.path.join(temp_dir, '%(playlist_index)s-%(title)s.%(ext)s')

            # Set format for playlist downloads (respect media_type and resolution)
            if media_type == 'video' and resolution:
                ydl_opts['format'] = f'bestvideo[height<={resolution}]+bestaudio/best'
                print_with_timestamp(f'Set playlist format to best video up to height {resolution}')
            else:
                ydl_opts['format'] = 'bestvideo+bestaudio/best' if media_type == 'video' else 'bestaudio/best'
                print_with_timestamp('Set playlist format to default best format')

            print_with_timestamp('Downloading playlist...')
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print_with_timestamp('Playlist download complete')

            print_with_timestamp('Creating ZIP archive...')
            zip_path = os.path.join(temp_dir, 'playlist.zip')
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in os.listdir(temp_dir):
                    if file != 'playlist.zip':
                        file_path = os.path.join(temp_dir, file)
                        zipf.write(file_path, arcname=file)
                        print_with_timestamp(f'Added {file} to zip')
            print_with_timestamp('ZIP archive created')

            zip_filename = f"{info.get('title', 'playlist').replace('/', '_')}.zip"
            response = FileResponse(
                open(zip_path, 'rb'),
                as_attachment=True,
                filename=zip_filename,
                content_type='application/zip'
            )
            response.temp_dir = temp_dir
            print_with_timestamp('Response ready with zip file, returning response')
            return response

        else:
            print_with_timestamp('Detected single video')
            ydl_opts['outtmpl'] = os.path.join(temp_dir, 'video.%(ext)s')

            if media_type == 'video' and resolution and download_type == '1':
                ydl_opts['format'] = f'bestvideo[height<={resolution}]+bestaudio/best'
                print_with_timestamp(f'Set format to best video up to height {resolution}')
            else:
                ydl_opts['format'] = 'bestvideo+bestaudio/best' if media_type == 'video' else 'bestaudio/best'
                print_with_timestamp(f'Set format to default best format')

            print_with_timestamp('Downloading single video...')
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print_with_timestamp('Download complete')

            files = [f for f in os.listdir(temp_dir) if f.startswith('video.')]
            print_with_timestamp(f'Files in temp_dir after download: {files}')
            if not files:
                raise FileNotFoundError("Downloaded file not found")

            downloaded_path = os.path.join(temp_dir, files[0])
            original_title = info.get('title', 'video').replace('/', '_').replace('\\', '_')
            filename = f"{original_title}.{files[0].split('.')[-1]}"
            print_with_timestamp(f'Preparing file response for {filename}')

            response = FileResponse(
                open(downloaded_path, 'rb'),
                as_attachment=True,
                filename=filename
            )
            response.temp_dir = temp_dir
            print_with_timestamp('Response ready with video file, returning response')
            return response

    except Exception as e:
        print_with_timestamp(f"Exception occurred: {str(e)}")
        logger.exception("Error during download")

        if os.path.exists(temp_dir):
            print_with_timestamp(f"Cleaning up temp dir at {temp_dir} due to error")
            shutil.rmtree(temp_dir)

        #testing:
        # Inside finally (after `except`)
        cookies_file = ydl_opts.get('cookiefile')
        if cookies_file and os.path.exists(cookies_file) and cookies_file != settings.YT_COOKIES_PATH:
            try:
                os.unlink(cookies_file)
            except:
                pass
            

        return render(request, 'downloader/download.html', {'error': str(e)})
