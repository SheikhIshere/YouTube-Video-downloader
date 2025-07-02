# 🎥 YouTube Video Downloader (Django + yt-dlp)

A **powerful**, **easy-to-use** web application built with **Django** and `yt-dlp`—allowing users to paste any YouTube link, choose the format, and download videos or audio instantly. No login required.


---

## 🚀 Features

- Paste any valid URL(Yt,GB, Insta, X)
- Select download format: video or audio  
- Smart format optimizer (best quality, mp4, m4a, etc.)  
- Automatically merges audio/video using `ffmpeg` if installed  
- Simple download interface with customizable output  
- No login or authentication required  

---

## 🛠️ Tech Stack

- **Backend**: Django  
- **Downloader**: yt-dlp  
- **Post-processing**: ffmpeg (optional, for merging)  
- **Frontend**: HTML + Tailwind CSS  
- **Utilities**: Python standard libs (shutil, tempfile, os)

---

## 📌 Prerequisites

- Python 3.9+  
- `yt-dlp` (install with `pip install -U yt-dlp`) 2  
- `ffmpeg` (optional, required to merge separate audio/video tracks)

---

## ⚙️ Live Links 🔗

```bash
https://online-video-downloader-by-imran.onrender.com/