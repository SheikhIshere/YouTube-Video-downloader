# [FILE NAME]: admin.py
# Configuration for Django admin interface
from django.contrib import admin
from .models import Download

@admin.register(Download)
class DownloadAdmin(admin.ModelAdmin):
    """
    Customizes how Download model appears in Django admin.
    Defines list display, filters, and search options.
    """
    # Fields to display in list view
    list_display = ('url', 'download_type', 'resolution', 'created_at', 'completed')
    
    # Filter options (right sidebar)
    list_filter = ('download_type', 'completed')
    
    # Searchable fields
    search_fields = ('url',)
    
    # Read-only fields (can't be edited)
    readonly_fields = ('created_at',)