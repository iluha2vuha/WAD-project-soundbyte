from django.db import models
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from django.conf import settings
from django.db import models
from django.core.validators import FileExtensionValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
import os

def profile_picture_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"profile_{instance.user.username}_{instance.user.id}.{ext}"
    return os.path.join('profile_pictures', filename)

def banner_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"banner_{instance.user.username}_{instance.user.id}.{ext}"
    return os.path.join('banners', filename)

class Profile(models.Model):
    USER_TYPE_CHOICES = [
        ('LISTENER', 'Music Listener'),
        ('ARTIST', 'Musician/Artist'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    slug = models.SlugField(unique=True)

    profile_picture = models.ImageField(
        upload_to=profile_picture_path,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif'])],
        blank=True, null=True)
    
    banner_image = models.ImageField(
        upload_to=banner_image_path,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],
        blank=True, null=True)
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='LISTENER')
    artist_name = models.CharField(max_length=100, blank=True, null=True)
    is_verified_artist = models.BooleanField(default=False)
    
    followers = models.ManyToManyField(User, related_name='following', blank=True)
    
    date_joined_profile = models.DateTimeField(auto_now_add=True)
    
    profile_views = models.PositiveIntegerField(default=0)
    total_likes_received = models.PositiveIntegerField(default=0)

    def save(self,*args,**kwargs):
        if not self.slug:
            max_length = self._meta.get_field('slug').max_length
            base_slug = (slugify(self.user.username) or 'profile')[:max_length]
            clean_slug = base_slug
            index = 1
            while Profile.objects.filter(slug=clean_slug).exclude(pk=self.pk).exists():
                suffix = f'-{index}'
                clean_slug = base_slug[:max_length - len(suffix)] + suffix
                index += 1
            self.slug = clean_slug
        super().save(*args,**kwargs)

    def __str__(self):
        return self.user.username
    
    class Meta:
        ordering = ['-date_joined_profile']
    
    def get_display_name(self):
        return self.artist_name if self.artist_name else self.user.username
    
    def is_artist(self):
        return self.user_type in ['ARTIST']
    
    def follower_count(self):
        return self.followers.count()
    
    def following_count(self):
        return self.user.following.count()

class Playlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    songs = models.ManyToManyField('Song')
    slug = models.SlugField()

    class Meta:
        unique_together = ('user', 'slug')

    def save(self,*args,**kwargs):
        if not self.slug:
            max_length = self._meta.get_field('slug').max_length
            base_slug = (slugify(self.title) or 'playlist')[:max_length]
            clean_slug = base_slug
            index = 1
            while Playlist.objects.filter(user=self.user, slug=clean_slug).exclude(pk=self.pk).exists():
                suffix = f'-{index}'
                clean_slug = base_slug[:max_length - len(suffix)] + suffix
                index += 1
            self.slug = clean_slug
        super().save(*args,**kwargs)

    def __str__(self):
        return self.title

class Genre(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Album(models.Model):
    #album data
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    cover_image = models.ImageField(upload_to='covers/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Song(models.Model):
    #song data
    title = models.CharField(max_length = 50)
    artist = models.CharField(max_length = 50)
    #genre can only be from premade genre list
    genres = models.ManyToManyField(Genre)
    #tags are optional dont need them (blank = true)
    tags = models.TextField(max_length=50, blank = True)
    #album must be an existing album in the database
    #there is a single album as a default if someone wants to
    #just realse one song
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    #files!!!
    audio_file = models.FileField(upload_to = 'songs/')
    #post data
    upload_date = models.DateTimeField(auto_now_add = True)
    download_count = models.IntegerField(default = 0)
    view_count = models.IntegerField(default = 0)
    like_count = models.IntegerField(default = 0)

    def __str__(self):
        return self.title
    
class Post(models.Model):
    text_content = models.TextField(blank=True)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    like_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'song')


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='comments')
    body = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following_links')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower_links')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')


class Download(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='downloads')
    created_at = models.DateTimeField(auto_now_add=True)


class ProfileView(models.Model):
    viewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='profile_views_made')
    profile_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_views_received')
    created_at = models.DateTimeField(auto_now_add=True)
