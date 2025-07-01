# [FILE NAME]: models.py
# Defines the database structure for tracking downloads
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Download(models.Model):
    """
    Database model to track download requests and their status.
    Stores information about what was downloaded, by whom, and when.
    """
    
    # Types of downloads we support
    DOWNLOAD_TYPES = (
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('playlist', 'Playlist'),
    )

    # Link to user (if authenticated)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,  # Delete downloads if user is deleted
        null=True,                 # Allow anonymous downloads
        blank=True
    )
    
    # URL of the downloaded content
    url = models.URLField(max_length=500)
    
    # Type of download (video/audio/playlist)
    download_type = models.CharField(
        max_length=10, 
        choices=DOWNLOAD_TYPES
    )
    
    # Video resolution (null for audio/playlist)
    resolution = models.PositiveIntegerField(null=True, blank=True)
    
    # Where the file is stored (not used in current implementation)
    file_path = models.CharField(max_length=500, blank=True)
    
    # When the download was requested
    created_at = models.DateTimeField(default=timezone.now)
    
    # Whether the download completed successfully
    completed = models.BooleanField(default=False)
    
    # File size in bytes
    file_size = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        """Human-readable representation of the download"""
        return f"{self.get_download_type_display()} - {self.url}"

    class Meta:
        """Metadata options for the model"""
        ordering = ['-created_at']  # Newest first
        verbose_name = 'Download'   # Singular name
        verbose_name_plural = 'Downloads'  # Plural name