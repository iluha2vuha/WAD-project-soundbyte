from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse, JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme
from .functions.file_manager import create_song
from .functions.search_function import search, sort_songs
from .forms import UserForm,ProfileForm,PlaylistForm
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
def upload_song(request):
    #must have album
    if request.method == 'POST':
        album_id = request.POST.get('album')
        if not album_id:
            #if no album return error to prevent crash
            return JsonResponse({'error': 'You must select an album'})
        album = Album.objects.get(id=album_id)
        #create song!!
        song = create_song(request.POST, request.FILES, album)
        #assign genres and add
        genre_ids = request.POST.getlist('genres')
        song.genres.set(genre_ids)
        return redirect('/search-page/')
    return JsonResponse({'error': 'Invalid request'})

@csrf_exempt
def search_songs(request):
    query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', '')
    #return songs that meet the search criteria
    songs = search(query)
    songs = sort_songs(songs, sort_by)
    return JsonResponse(list(songs.values()), safe=False)

@login_required
def upload_page(request):
    genres = Genre.objects.all()
    albums = Album.objects.all()
    return render(request, 'soundbytes_auth/upload.html', {'genres': genres, 'albums': albums})

def search_page(request):
    query = request.GET.get('q', '')
    genre = request.GET.get('genre')
    sort_by = request.GET.get('sort', '')
    content_type = request.GET.get('type', 'all')
    genres = Genre.objects.all()
    #songs
    songs = search(query)
    if genre:
        songs = songs.filter(genres__name=genre)
    #posts
    posts = Post.objects.all()
    if query:
        posts = posts.filter(text_content__icontains=query)
    #all sort (automatically sorts by newest)
    if not sort_by or sort_by == 'new':
        songs = songs.order_by('-upload_date')
        posts = posts.order_by('-created_at')
        songs = list(songs)
        posts = list(posts)
        results = []
        if content_type == 'songs':
            results = [{'type': 'song', 'data': s} for s in songs]
        elif content_type == 'posts':
            results = [{'type': 'post', 'data': p} for p in posts]
        else:
            #mix posts and songs
            max_len = max(len(songs), len(posts))
            for i in range(max_len):
                if i < len(songs):
                    results.append({'type': 'song', 'data': songs[i]})
                if i < len(posts):
                    results.append({'type': 'post', 'data': posts[i]})
    #sort by likes
    elif sort_by == 'likes':
        songs = list(songs.order_by('-like_count'))
        posts = list(posts.order_by('-like_count'))
        results = []
        #{comment here}
        if content_type == 'songs':
            results = [{'type': 'song', 'data': s} for s in songs]
        elif content_type == 'posts':
            results = [{'type': 'post', 'data': p} for p in posts]
        else:
            #{comment here}
            max_len = max(len(songs), len(posts))
            for i in range(max_len):
                if i < len(songs):
                    results.append({'type': 'song', 'data': songs[i]})
                if i < len(posts):
                    results.append({'type': 'post', 'data': posts[i]})
    #sort by views
    elif sort_by == 'views':
        songs = songs.order_by('-view_count')
        results = [{'type': 'song', 'data': s} for s in songs]
    #sort by downloads
    elif sort_by == 'downloads':
        songs = songs.order_by('-download_count')
        results = [{'type': 'song', 'data': s} for s in songs]
    else:
        results = []
    return render(request, 'soundbytes_auth/search.html', {'results': results, 'genres': genres})

def stream_song(request, song_id):
    song = get_object_or_404(Song, id=song_id)
    #increase view count on stream
    song.view_count += 1
    song.save()
    #play song
    return FileResponse(song.audio_file.open(), content_type='audio/mpeg')

@login_required
def create_album(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        artist = request.POST.get('artist')
        cover = request.FILES.get('cover_image')
        #create album with data above got from page
        Album.objects.create(
            title=title,
            artist=artist,
            cover_image=cover
        )
        return redirect('/upload-page/')
    return render(request, 'soundbytes_auth/create_album.html')

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
def upload(request):
    if request.method == 'POST':
        content_type = request.POST.get('content_type')
        if content_type == 'song':
            return upload_song(request)
        elif content_type == 'post':
            return upload_post(request)
        else:
            return JsonResponse({'error': f'Invalid content type: {content_type}'})
    return JsonResponse({'error': 'Invalid request'})

def upload_post(request):
    text = request.POST.get('text_content')
    image = request.FILES.get('image_file')
    if not text and not image:
        return JsonResponse({'error': 'Post must contain text or an image'})
    Post.objects.create(text_content=text, image=image)
    return redirect('/search-page/')

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
        song_id = request.POST.get("song_id")
        slug = request.POST.get("playlist_slug")
        song = get_object_or_404(Song, id=song_id)
        playlist = get_object_or_404(Playlist, slug=slug, user=user)
        playlist.songs.add(song)
        return redirect("soundbytes:profile", username=user.username)
