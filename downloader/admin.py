from django.contrib import admin
from .models import Download

@admin.register(Download)
class DownloadAdmin(admin.ModelAdmin):
    list_display = ('url', 'download_type', 'resolution', 'created_at', 'completed')
    list_filter = ('download_type', 'completed')
    search_fields = ('url',)
    readonly_fields = ('created_at',)