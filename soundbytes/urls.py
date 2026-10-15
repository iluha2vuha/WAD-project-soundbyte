from django.urls import path
from soundbytes import views

app_name = 'soundbytes'

#all urls i used, please do not remove anything from this list!!
urlpatterns = [
    path('', views.landing, name='landing'),
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('home/', views.home, name='home'),
    path('signout/', views.signout, name='signout'),
    path('upload/', views.upload, name='upload'),
    path('search/', views.search_songs, name='search_songs'),
    path('upload-page/', views.upload_page, name='upload_page'),
    path('search-page/', views.search_page, name='search_page'),
    path('stream/<int:song_id>/', views.stream_song, name='stream_song'),
    path('download/<int:song_id>/', views.download_song, name='download_song'),
    path('like/<int:song_id>/', views.toggle_like, name='toggle_like'),
    path('comment/<int:song_id>/', views.add_comment, name='add_comment'),
    path('create-album/', views.create_album, name='create_album'),
    path('album/<int:album_id>/', views.album_page, name='album_page'),
    path('trending/', views.trending_page, name='trending'),
    path('top/', views.top_page, name='top'),
    path('creatordb/', views.creator_dashboard, name='creator_dashboard'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('follow/<str:username>/', views.toggle_follow, name='toggle_follow'),
    path('playlists/<str:username>/', views.playlists, name='playlists'),
    path('playlists/<str:username>/<slug:slug>/', views.playlist, name='playlist'),
    path('add_to_playlist/', views.add_to_playlist,name='add_to_playlist')
]
