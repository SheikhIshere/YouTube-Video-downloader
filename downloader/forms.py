from django import forms

class DownloadForm(forms.Form):
    DOWNLOAD_TYPE = (
        ('1', 'Single Video'),
        ('2', 'Playlist'),
    )
    
    download_type = forms.ChoiceField(
        choices=DOWNLOAD_TYPE, 
        widget=forms.RadioSelect,
        label='Download Type'
    )
    url = forms.URLField(
        label='Video/Playlist URL',
        widget=forms.URLInput(attrs={'placeholder': 'Enter video/playlist URL'})
    )