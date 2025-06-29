from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Download(models.Model):
    DOWNLOAD_TYPES = (
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('playlist', 'Playlist'),
    )

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    url = models.URLField(max_length=500)
    download_type = models.CharField(
        max_length=10, 
        choices=DOWNLOAD_TYPES
    )
    resolution = models.PositiveIntegerField(null=True, blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    completed = models.BooleanField(default=False)
    file_size = models.BigIntegerField(null=True, blank=True)  # in bytes

    def __str__(self):
        return f"{self.get_download_type_display()} - {self.url}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Download'
        verbose_name_plural = 'Downloads'