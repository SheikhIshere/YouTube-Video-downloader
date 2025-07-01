# [FILE NAME]: forms.py
# Defines the form structure for user input
from django import forms

class DownloadForm(forms.Form):
    """
    Form for users to enter download information.
    Contains:
    - Download type (single video or playlist)
    - URL of the content to download
    """
    
    # Choices for download type radio buttons
    DOWNLOAD_TYPE = (
        ('1', 'Single Video'),  # '1' is stored in database, 'Single Video' is displayed
        ('2', 'Playlist'),
    )
    
    # Radio select field for choosing download type
    download_type = forms.ChoiceField(
        choices=DOWNLOAD_TYPE, 
        widget=forms.RadioSelect,  # Display as radio buttons
        label='Download Type'       # Field label
    )
    
    # URL input field with placeholder text
    url = forms.URLField(
        label='Video/Playlist URL',
        widget=forms.URLInput(attrs={'placeholder': 'Enter video/playlist URL'})
    )