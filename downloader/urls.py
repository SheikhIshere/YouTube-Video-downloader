# [FILE NAME]: urls.py
# Defines the URL routes for this app
from django.urls import path
from . import views

# Namespace for this app's URLs
app_name = 'downloader'

# URL patterns mapping URLs to views
urlpatterns = [
    path('', views.index, name='index'),          # Home page/form
    path('preview/', views.preview, name='preview'),  # Content preview
    path('download/', views.download, name='download'),  # Download handler
]