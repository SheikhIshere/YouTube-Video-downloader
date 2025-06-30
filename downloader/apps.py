from django.apps import AppConfig
import os
import json
from django.conf import settings

class DownloaderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'downloader'

    def ready(self):
        cookie_data = os.getenv("YT_COOKIES")
        if cookie_data:
            try:
                # Parse the JSON string from environment
                cookies = json.loads(cookie_data)
                cookies_path = os.path.join(settings.BASE_DIR, 'cookies.txt')

                # Write cookies in Netscape format for yt-dlp
                with open(cookies_path, 'w', encoding='utf-8') as f:
                    for cookie in cookies:
                        line = "\t".join([
                            cookie.get("domain", ""),
                            "TRUE" if cookie.get("hostOnly") == False else "FALSE",
                            cookie.get("path", "/"),
                            cookie.get("secure", False) and "TRUE" or "FALSE",
                            str(int(cookie.get("expirationDate", 0))) if cookie.get("expirationDate") else "0",
                            cookie.get("name", ""),
                            cookie.get("value", ""),
                        ])
                        f.write(line + "\n")

            except json.JSONDecodeError:
                # If YT_COOKIES is not valid JSON, just write raw string (fallback)
                cookies_path = os.path.join(settings.BASE_DIR, 'cookies.txt')
                with open(cookies_path, 'w', encoding='utf-8') as f:
                    f.write(cookie_data)
