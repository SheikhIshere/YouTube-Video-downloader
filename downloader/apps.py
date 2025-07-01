# [FILE NAME]: apps.py
# This file configures the Django app and handles initial setup tasks
from django.apps import AppConfig
import os
from django.conf import settings

class DownloaderConfig(AppConfig):
    # Database configuration - uses big integers for primary keys
    default_auto_field = 'django.db.models.BigAutoField'
    
    # Name of this app (must match the app folder name)
    name = 'downloader'

    def ready(self):
        """
        This method runs when Django starts. We use it to set up YouTube cookies.
        Cookies can be provided via environment variable or file.
        """
        # 1. Get cookies from environment variable if available
        cookie_data = os.getenv("YT_COOKIES")
        
        # 2. Determine where to save cookies file (default location or custom from settings)
        cookies_path = getattr(settings, 'YT_COOKIES_PATH', os.path.join(settings.BASE_DIR, 'cookies.txt'))
        
        # 3. If we have cookie data, save it to file
        if cookie_data:
            try:
                # Write cookies to file using UTF-8 encoding
                with open(cookies_path, 'w', encoding='utf-8') as f:
                    f.write(cookie_data)
                print(f"[YT-COOKIES] Cookies written to: {cookies_path}")
            except Exception as e:
                # Handle any errors during file writing
                print(f"[YT-COOKIES] Failed to write cookies: {e}")