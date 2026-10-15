from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Album, Playlist, Post, Profile, Song

class BootstrapModelForm(forms.ModelForm):
    """Apply Bootstrap controls consistently to the existing model forms."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = (
                'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            )
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs['rows'] = 4


class UserForm(BootstrapModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username','email','password',)

    def clean(self):
        data = super().clean()
        password = data.get("password")
        confirm_password = data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Password Mismatch")
        return data

class ProfileForm(BootstrapModelForm):
    class Meta:
        model = Profile
        fields = ('artist_name','profile_picture','user_type','bio')

class PlaylistForm(BootstrapModelForm):
    class Meta:
        model = Playlist
        fields = ['title']  # only the playlist title is needed
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Playlist Title'}),
        }
        labels = {
            'title': 'Playlist Name',
        }


class AlbumForm(BootstrapModelForm):
    # Covers were optional in the original creation flow.
    cover_image = forms.ImageField(required=False, label='Cover image')

    class Meta:
        model = Album
        fields = ['title', 'artist', 'cover_image']
        labels = {'title': 'Album title'}


class SongUploadForm(BootstrapModelForm):
    class Meta:
        model = Song
        fields = ['title', 'artist', 'album', 'genres', 'tags', 'audio_file']
        labels = {'title': 'Track title', 'audio_file': 'Audio file'}
        widgets = {'tags': forms.TextInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['genres'].required = False
        self.fields['album'].empty_label = 'Select an album'

    def clean_tags(self):
        return ','.join(tag.strip().lower() for tag in self.cleaned_data['tags'].split(',') if tag.strip())


class PostUploadForm(BootstrapModelForm):
    image_file = forms.ImageField(required=False, label='Image (optional)')

    class Meta:
        model = Post
        fields = ['text_content', 'image_file']
        labels = {'text_content': 'Your post'}

    def clean(self):
        data = super().clean()
        if not data.get('text_content') and not data.get('image_file'):
            raise forms.ValidationError('Post must contain text or an image.')
        return data
