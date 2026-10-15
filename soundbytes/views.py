from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse, JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme
from .functions.search_function import search, sort_songs
from .forms import AlbumForm, PlaylistForm, PostUploadForm, ProfileForm, SongUploadForm, UserForm
from .models import Comment, Download, Follow, Genre, Like, Song, Album, User, Profile, Post, ProfileView, Playlist

def landing(request):

    context_dict={}
    context_dict['boldmessage']='hi'

    response = render(request, 'soundbytes_base/landing.html', context = context_dict)
    return response

def signup(request):
    registered = False
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = ProfileForm(request.POST, request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            registered = True
        else:
            print(user_form.errors, profile_form.errors)
    else:
        user_form = UserForm()
        profile_form = ProfileForm()
    return render(request,'soundbytes_base/signup.html',
                  context = {'user_form':user_form,
                             'profile_form':profile_form,
                             'registered':registered})
def signin(request):
    next_url = request.POST.get('next', request.GET.get('next', ''))
    if not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        next_url = reverse('soundbytes:home')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request,user)
                return redirect(next_url)
            else:
                return HttpResponse("Your Soundbytes account is diabled")
        else:
            error = 'Invalid username or password.'
    return render(request, 'soundbytes_base/signin.html', {'next': next_url, 'error': error})
    
#Auth only below
    
@login_required
def signout(request):
    logout(request)
    return redirect(reverse('soundbytes:landing'))

def home(request):
    recent_songs = Song.objects.order_by('-upload_date')[:6]
    trending_songs = sorted(
        Song.objects.all(),
        key=lambda song: (song.like_count * 3) + (song.view_count * 2) + (song.download_count * 4),
        reverse=True,
    )[:5]
    recent_posts = Post.objects.order_by('-created_at')[:4]

    context = {
        'recent_songs': recent_songs,
        'trending_songs': trending_songs,
        'recent_posts': recent_posts,
    }
    return render(request, 'soundbytes_auth/home.html', context)


@csrf_exempt
def search_songs(request):
    query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', '')
    #return songs that meet the search criteria
    songs = search(query)
    songs = sort_songs(songs, sort_by)
    return JsonResponse(list(songs.values()), safe=False)

def _render_upload(request, *, song_form=None, post_form=None, content_type='song', error=None):
    return render(request, 'soundbytes_auth/upload.html', {
        'song_form': song_form if song_form is not None else SongUploadForm(auto_id='id_song_%s'),
        'post_form': post_form if post_form is not None else PostUploadForm(auto_id='id_post_%s'),
        'content_type': content_type, 'upload_error': error,
    })


@login_required
def upload_page(request):
    return _render_upload(request)

def search_page(request):
    query = request.GET.get('q', '')
    genre = request.GET.get('genre', '')
    sort_by = request.GET.get('sort', '')
    content_type = request.GET.get('type', 'all')
    song_ordering = {
        '': '-upload_date', 'new': '-upload_date', 'likes': '-like_count',
        'views': '-view_count', 'downloads': '-download_count',
    }
    if sort_by not in song_ordering:
        sort_by = ''
    if content_type not in {'all', 'songs', 'posts'}:
        content_type = 'all'

    songs = search(query)
    if genre:
        songs = songs.filter(genres__name=genre)
    songs = list(songs.order_by(song_ordering[sort_by]))
    posts = Post.objects.all()
    if query:
        posts = posts.filter(text_content__icontains=query)
    posts = list(posts.order_by('-like_count' if sort_by == 'likes' else '-created_at'))

    if content_type == 'posts':
        # Posts have no view/download counters, so keep them in newest order.
        results = [{'type': 'post', 'data': post} for post in posts]
    elif content_type == 'songs' or sort_by in {'views', 'downloads'}:
        results = [{'type': 'song', 'data': song} for song in songs]
    else:
        results = []
        for index in range(max(len(songs), len(posts))):
            if index < len(songs):
                results.append({'type': 'song', 'data': songs[index]})
            if index < len(posts):
                results.append({'type': 'post', 'data': posts[index]})

    return render(request, 'soundbytes_auth/search.html', {
        'results': results, 'genres': Genre.objects.all(), 'query': query,
        'selected_genre': genre, 'content_type': content_type, 'sort_by': sort_by,
    })

def stream_song(request, song_id):
    song = get_object_or_404(Song, id=song_id)
    #increase view count on stream
    song.view_count += 1
    song.save()
    #play song
    return FileResponse(song.audio_file.open(), content_type='audio/mpeg')

@login_required
def create_album(request):
    form = AlbumForm(request.POST if request.method == 'POST' else None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('soundbytes:upload_page')
    return render(request, 'soundbytes_auth/create_album.html', {'form': form})

def album_page(request, album_id):
    #displays songs in that album
    album = get_object_or_404(Album, id=album_id)
    songs = Song.objects.filter(album=album)
    return render(request, 'soundbytes_auth/album.html', {'album': album,'songs': songs})

def trending_page(request):
    results = []
    # song scores
    songs = Song.objects.all()
    for song in songs:
        score = ((song.like_count * 3) + (song.view_count * 2) + (song.download_count * 4))
        results.append({'type': 'song', 'data': song, 'score': score})
    # score posts
    posts = Post.objects.all()
    for post in posts:
        score = post.like_count * 5
        results.append({'type': 'post', 'data': post, 'score': score})
    # find top ten
    results = sorted(results, key=lambda x: x['score'], reverse=True)[:10]
    return render(request, 'soundbytes_auth/trending.html', {'results': results})

def top_page(request):
    return redirect(reverse('soundbytes:trending'))

@login_required
@require_POST
def upload(request):
    content_type = request.POST.get('content_type')
    if content_type == 'song':
        form = SongUploadForm(request.POST, request.FILES, auto_id='id_song_%s')
        if form.is_valid():
            song = form.save()
            return redirect('soundbytes:album_page', album_id=song.album_id)
        return _render_upload(request, song_form=form)
    if content_type == 'post':
        form = PostUploadForm(request.POST, request.FILES, auto_id='id_post_%s')
        if form.is_valid():
            post = form.save(commit=False)
            post.image = form.cleaned_data['image_file']
            post.save()
            return redirect('soundbytes:search_page')
        return _render_upload(request, post_form=form, content_type='post')
    return _render_upload(request, error='Select a valid upload type.')

# Update your profile_view to include analytics
def profile(request, username):
    logged=request.user
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)
    songs = Song.objects.filter(artist=user.username).order_by('-upload_date')
    recent_comments = Comment.objects.filter(song__artist=user.username).order_by('-created_at')[:10]
    total_song_views = sum(song.view_count for song in songs)
    total_song_downloads = sum(song.download_count for song in songs)
    total_song_likes = sum(song.like_count for song in songs)
    total_song_comments = Comment.objects.filter(song__artist=user.username).count()
    top_liked_song = songs.order_by('-like_count', '-view_count').first()
    top_viewed_song = songs.order_by('-view_count', '-like_count').first()
    top_downloaded_song = songs.order_by('-download_count', '-view_count').first()
    # Guests can view an artist without querying playlists for AnonymousUser.
    playlists = Playlist.objects.filter(user=logged) if logged.is_authenticated else Playlist.objects.none()
    
    # Increment profile views
    if request.user.is_authenticated and request.user != user:
        profile.profile_views += 1
        profile.save(update_fields=['profile_views'])
        ProfileView.objects.create(viewer=request.user, profile_user=user)
    
    # Check if user is following
    is_following = request.user.is_authenticated and request.user in profile.followers.all()
    
    if profile.is_artist():
        context = {
            'profile_user': user,
            'profile': profile,
            'songs': songs,
            'recent_comments': recent_comments,
            'total_song_views': total_song_views,
            'total_song_downloads': total_song_downloads,
            'total_song_likes': total_song_likes,
            'total_song_comments': total_song_comments,
            'top_liked_song': top_liked_song,
            'top_viewed_song': top_viewed_song,
            'top_downloaded_song': top_downloaded_song,
            'is_own_profile': request.user.is_authenticated and request.user == user,
            'is_following': is_following,
            'playlists':playlists,
            'logged':logged
        }
    else:
        context = {
            'profile_user': user,
            'profile': profile,
            'songs': songs,
            'recent_comments': recent_comments,
            'total_song_views': total_song_views,
            'total_song_downloads': total_song_downloads,
            'total_song_likes': total_song_likes,
            'total_song_comments': total_song_comments,
            'top_liked_song': top_liked_song,
            'top_viewed_song': top_viewed_song,
            'top_downloaded_song': top_downloaded_song,
            'is_own_profile': request.user.is_authenticated and request.user == user,
            'is_following': is_following,
            'playlists':playlists,
        }
    return render(request,'soundbytes_auth/profile.html', context)

def download_song(request, song_id):
    song = get_object_or_404(Song, id=song_id)
    Download.objects.create(
        user=request.user if request.user.is_authenticated else None,
        song=song,
    )
    song.download_count += 1
    song.save()
    filename = song.audio_file.name.split('/')[-1]
    return FileResponse(song.audio_file.open(), as_attachment=True, filename=filename)


@login_required
def toggle_like(request, song_id):
    if request.method != 'POST':
        return redirect(reverse('soundbytes:search_page'))

    song = get_object_or_404(Song, id=song_id)
    like, created = Like.objects.get_or_create(user=request.user, song=song)

    if created:
        song.like_count += 1
    else:
        like.delete()
        song.like_count = max(0, song.like_count - 1)

    song.save()
    return redirect(request.META.get('HTTP_REFERER', reverse('soundbytes:search_page')))


@login_required
def add_comment(request, song_id):
    if request.method == 'POST':
        song = get_object_or_404(Song, id=song_id)
        body = request.POST.get('body', '').strip()
        if body:
            Comment.objects.create(user=request.user, song=song, body=body)

    return redirect(request.META.get('HTTP_REFERER', reverse('soundbytes:search_page')))


@login_required
def toggle_follow(request, username):
    target_user = get_object_or_404(User, username=username)

    if target_user == request.user:
        return redirect(reverse('soundbytes:profile', args=[target_user.username]))

    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        following=target_user,
    )

    if created:
        target_user.profile.followers.add(request.user)
    else:
        follow.delete()
        target_user.profile.followers.remove(request.user)

    return redirect(reverse('soundbytes:profile', args=[target_user.username]))


@login_required
def creator_dashboard(request):
    user_songs = Song.objects.filter(artist=request.user.username).order_by('-upload_date')
    summary = {
        'songs': [
            {
                'id': song.id,
                'title': song.title,
                'album': song.album.title,
                'views': song.view_count,
                'downloads': song.download_count,
                'likes': song.like_count,
            }
            for song in user_songs
        ],
        'total_views': sum(song.view_count for song in user_songs),
        'total_downloads': sum(song.download_count for song in user_songs),
        'total_likes': sum(song.like_count for song in user_songs),
        'total_comments': Comment.objects.filter(song__in=user_songs).count(),
        'follower_count': Follow.objects.filter(following=request.user).count(),
        'profile_view_count': ProfileView.objects.filter(profile_user=request.user).count(),
    }
    return JsonResponse(summary)

@login_required
def playlists(request, username):
    user = get_object_or_404(User, username=username)

    if request.method == 'POST':
        form = PlaylistForm(request.POST)
        if form.is_valid():
            playlist = form.save(commit=False)
            playlist.user = request.user  # assign the current user
            playlist.save()  # slug is generated automatically in model
            return redirect('soundbytes:playlists', username=request.user.username)
    else:
        form = PlaylistForm()

    context = {
            'user': user,
            'playlists': Playlist.objects.filter(user=user).order_by('title'),
            'form':form
    }
    return render(request, 'soundbytes_auth/playlists.html', context)

@login_required
def playlist(request, username, slug):
    user = get_object_or_404(User, username=username)
    playlist = get_object_or_404(Playlist,user=user,slug=slug)
    songs = playlist.songs.all()
    results=[]
    for song in songs:
        results.append({'data': song})
    context={
        'user':user,
        'playlist':playlist,
        'songs':results
        }
    return render(request, 'soundbytes_auth/playlist.html', context)

@login_required
@require_POST
def add_to_playlist(request):
    user = request.user
    if request.method == "POST":
        try:
            song_id = int(request.POST.get("song_id", ""))
        except (TypeError, ValueError):
            raise Http404("Song not found")
        slug = request.POST.get("playlist_slug")
        song = get_object_or_404(Song, id=song_id)
        playlist = get_object_or_404(Playlist, slug=slug, user=user)
        playlist.songs.add(song)
        return redirect("soundbytes:profile", username=user.username)
