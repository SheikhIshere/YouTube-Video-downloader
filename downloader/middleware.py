# [FILE NAME]: middleware.py
# Cleans up temporary files after each request
import shutil
import os

class TempFileCleanupMiddleware:
    """
    Middleware that deletes temporary files after the response is sent.
    Prevents server from filling up with temporary download files.
    """
    
    def __init__(self, get_response):
        # Standard Django middleware initialization
        self.get_response = get_response

    def __call__(self, request):
        # Process the request and get the response
        response = self.get_response(request)
        
        # Check if response has a temp_dir attribute and if it exists
        if hasattr(response, 'temp_dir') and os.path.exists(response.temp_dir):
            try:
                # Recursively delete the temporary directory
                shutil.rmtree(response.temp_dir)
            except Exception as e:
                # Silently fail (in production you'd want logging here)
                pass
        return response