from django.conf import settings
import shutil
from django.shortcuts import render, redirect
from django.http import FileResponse
from .forms import DownloadForm
from .utils import clean_url, is_valid_url, is_youtube, get_video_info
import os
import yt_dlp
import tempfile
from django.http import FileResponse


class DeleteDirFileResponse(FileResponse):
    def __init__(self, *args, temp_dir=None, **kwargs):
        self.temp_dir = temp_dir
        super().__init__(*args, **kwargs)

    def close(self):
        super().close()
        if self.temp_dir:
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass



def index(request):
    if request.method == 'POST':
        form = DownloadForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            download_type = form.cleaned_data['download_type']
            
            if not is_valid_url(url):
                form.add_error('url', 'Invalid URL')
                return render(request, 'downloader/index.html', {'form': form})
            
            # Clean YouTube URLs
            if download_type == '1' and is_youtube(url):
                url = clean_url(url)
            
            request.session['download_info'] = {
                'url': url,
                'download_type': download_type
            }
            
            return redirect('downloader:preview')
    else:
        form = DownloadForm()
    
    return render(request, 'downloader/index.html', {'form': form})

def preview(request):
    if not request.session.get('download_info'):
        return redirect('downloader:index')
    
    url = request.session['download_info']['url']
    download_type = request.session['download_info']['download_type']
    
    try:
        info = get_video_info(url)
        
        # Handle playlists
        if download_type == '2' and 'entries' in info:
            videos = []
            for entry in info['entries']:
                if entry:
                    videos.append({
                        'title': entry.get('title', 'Untitled'),
                        'thumbnail': entry.get('thumbnail'),
                        'id': entry.get('id')
                    })
            context = {
                'type': 'playlist',
                'title': info.get('title', 'Untitled Playlist'),
                'thumbnail': info.get('thumbnail'),
                'videos': videos,
                'url': url
            }
        else:
            # Handle single video
            formats = []
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none' and f.get('height'):
                    formats.append({
                        'height': f['height'],
                        'ext': f['ext'],
                        'filesize': f.get('filesize') or f.get('filesize_approx', 0)
                    })
            
            # Remove duplicates and sort
            formats = sorted(
                {f['height']: f for f in formats}.values(),
                key=lambda x: x['height'],
                reverse=True
            )
            
            context = {
                'type': 'video',
                'title': info.get('title', 'Untitled Video'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration'),
                'formats': formats,
                'url': url
            }
        
        return render(request, 'downloader/preview.html', context)
    
    except Exception as e:
        return render(request, 'downloader/index.html', {
            'form': DownloadForm(),
            'error': f'Error retrieving video info: {str(e)}'
        })



def download(request):
    if request.method != 'POST' or not request.session.get('download_info'):
        return redirect('downloader:index')

    url = request.session['download_info']['url']
    download_type = request.session['download_info']['download_type']
    media_type = request.POST.get('media_type', 'video')
    resolution = request.POST.get('resolution')

    try:
        ydl_opts = {
            'cookiefile': os.path.join(settings.BASE_DIR, 'cookies.txt'),
            'quiet': True,
            'no_warnings': True,
            'headers': {
                'User-Agent': 'Mozilla/5.0',
            },

        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if 'entries' in info:
                return render(request, 'downloader/download.html', {
                    'error': 'Playlist downloads are not supported yet. Please select a single video.'
                })

            original_title = info.get('title', 'video').replace('/', '_').replace('\\', '_')
            ext = 'mp4' if media_type == 'video' else 'mp3'
            filename = f"{original_title}.{ext}"

            ydl_opts = {
                'cookiefile': os.path.join(settings.BASE_DIR, 'cookies.txt'),
                'quiet': True,
                'no_warnings': True,
                'headers': {
                    'User-Agent': 'Mozilla/5.0',
                },
            }

            if media_type == 'video':
                if resolution and download_type == '1':
                    ydl_opts['format'] = f'bestvideo[height<={resolution}][ext=mp4]+bestaudio[ext=m4a]'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }]
            else:
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]

            # Create temporary directory manually
            tmpdir = tempfile.mkdtemp()
            ydl_opts['outtmpl'] = os.path.join(tmpdir, '%(title)s.%(ext)s')

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Find downloaded file
            downloaded_files = [f for f in os.listdir(tmpdir) if not f.endswith('.part')]
            if not downloaded_files:
                shutil.rmtree(tmpdir)
                return render(request, 'downloader/download.html', {'error': 'File not found after download'})

            downloaded_path = os.path.join(tmpdir, downloaded_files[0])

            if media_type == 'audio':
                mp3_files = [f for f in os.listdir(tmpdir) if f.endswith('.mp3')]
                if mp3_files:
                    downloaded_path = os.path.join(tmpdir, mp3_files[0])

            # Open file and send response, deleting temp dir after response close
            f = open(downloaded_path, 'rb')
            response = DeleteDirFileResponse(
                f,
                as_attachment=True,
                filename=filename,
                temp_dir=tmpdir
            )
            return response

    except Exception as e:
        return render(request, 'downloader/download.html', {'error': str(e)})
    
