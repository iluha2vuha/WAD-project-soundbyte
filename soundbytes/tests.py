"""Regression tests for browsing, sign-in and playlist failures from the review."""
from pathlib import Path
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Album, Like, Playlist, Profile, Song


class BrowsingAndPlaylistTests(TestCase):
    @classmethod
    def setUpClass(cls):
        media = cls.enterClassContext(tempfile.TemporaryDirectory())
        cls.enterClassContext(override_settings(MEDIA_ROOT=media))
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        cls.artist = User.objects.create_user('artist', password='Test-password-2026')
        Profile.objects.create(user=cls.artist, user_type='ARTIST')
        cls.listener = User.objects.create_user('listener', password='Test-password-2026')
        Profile.objects.create(user=cls.listener)
        cls.album = Album.objects.create(title='Test album', artist='artist')
        cls.audio_bytes = (Path(__file__).resolve().parent.parent / 'sample_data/audio/gossip.mp3').read_bytes()
        cls.song = Song.objects.create(
            title='Test song', artist='artist', album=cls.album,
            audio_file=SimpleUploadedFile('test.mp3', cls.audio_bytes, content_type='audio/mpeg'),
        )
        cls.playlist = Playlist.objects.create(user=cls.listener, title='My favourites')

    def test_guest_can_browse_public_pages(self):
        for name, args in [
            ('landing', []), ('home', []), ('search_page', []), ('trending', []),
            ('profile', ['artist']), ('profile', ['listener']), ('album_page', [self.album.pk]),
        ]:
            with self.subTest(page=name, args=args):
                response = self.client.get(reverse(f'soundbytes:{name}', args=args))
                self.assertEqual(response.status_code, 200)
                if name != 'landing':
                    self.assertContains(response, 'Sign In')
                    self.assertNotContains(response, '>My Profile<')

    def test_guest_can_find_music(self):
        response = self.client.get(reverse('soundbytes:search_page'), {'q': 'Test song'})
        self.assertContains(response, self.song.title)
        self.assertNotContains(response, 'Like / Unlike')

    def test_guest_can_stream_audio(self):
        response = self.client.get(reverse('soundbytes:stream_song', args=[self.song.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'audio/mpeg')
        self.assertEqual(b''.join(response.streaming_content), self.audio_bytes)
        response.close()
        self.song.refresh_from_db()
        self.assertEqual(self.song.view_count, 1)

    def test_guest_can_download_audio(self):
        response = self.client.get(reverse('soundbytes:download_song', args=[self.song.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), self.audio_bytes)
        response.close()
        self.assertIsNone(self.song.downloads.get().user)

    def test_missing_content_returns_404(self):
        for name, args in [('stream_song', [999]), ('album_page', [999]), ('profile', ['missing'])]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(f'soundbytes:{name}', args=args)).status_code, 404)

    def test_guest_cannot_upload_or_create_an_album(self):
        for name in ['upload_page', 'create_album', 'upload']:
            with self.subTest(page=name):
                url = reverse(f'soundbytes:{name}')
                response = self.client.post(url, {}) if name == 'upload' else self.client.get(url)
                self.assertRedirects(response, f"{reverse('soundbytes:signin')}?next={url}")
        self.assertEqual(Album.objects.count(), 1)
        self.assertEqual(Song.objects.count(), 1)

    def test_guest_cannot_like_or_comment(self):
        for name in ['toggle_like', 'add_comment']:
            with self.subTest(action=name):
                url = reverse(f'soundbytes:{name}', args=[self.song.pk])
                self.assertRedirects(self.client.post(url, {'body': 'Hello'}), f"{reverse('soundbytes:signin')}?next={url}")
        self.assertFalse(Like.objects.exists())
        self.assertFalse(self.song.comments.exists())

    def test_signin_returns_to_requested_page(self):
        destination = reverse('soundbytes:upload_page')
        response = self.client.post(reverse('soundbytes:signin'), {
            'username': 'listener', 'password': 'Test-password-2026', 'next': destination,
        })
        self.assertRedirects(response, destination)

    def test_signin_rejects_external_redirects(self):
        response = self.client.post(reverse('soundbytes:signin'), {
            'username': 'listener', 'password': 'Test-password-2026', 'next': 'https://example.com/',
        })
        self.assertRedirects(response, reverse('soundbytes:home'))

    def test_invalid_signin_renders_form_with_error(self):
        response = self.client.post(reverse('soundbytes:signin'), {'username': 'listener', 'password': 'incorrect'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password.')
        self.assertContains(response, 'name="password"')

    def test_profile_submits_actual_playlist_slug(self):
        self.client.force_login(self.listener)
        response = self.client.get(reverse('soundbytes:profile', args=['artist']))
        self.assertContains(response, f'<option value="{self.playlist.slug}">')
        response = self.client.post(reverse('soundbytes:add_to_playlist'), {
            'song_id': self.song.pk, 'playlist_slug': self.playlist.slug,
        })
        self.assertRedirects(response, reverse('soundbytes:profile', args=['listener']))
        self.assertTrue(self.playlist.songs.filter(pk=self.song.pk).exists())

    def test_cannot_add_song_to_another_users_playlist(self):
        self.client.force_login(self.artist)
        response = self.client.post(reverse('soundbytes:add_to_playlist'), {
            'song_id': self.song.pk, 'playlist_slug': self.playlist.slug,
        })
        self.assertEqual(response.status_code, 404)
        self.assertFalse(self.playlist.songs.exists())

    def test_add_to_playlist_requires_post(self):
        self.client.force_login(self.listener)
        self.assertEqual(self.client.get(reverse('soundbytes:add_to_playlist')).status_code, 405)

    def test_create_playlist_redirects_to_own_playlists(self):
        self.client.force_login(self.listener)
        url = reverse('soundbytes:playlists', args=['listener'])
        response = self.client.post(url, {'title': 'New mix'})
        self.assertRedirects(response, url)
        self.assertTrue(Playlist.objects.filter(user=self.listener, title='New mix').exists())

    def test_navigation_keeps_signed_in_user_when_viewing_another_playlist(self):
        self.client.force_login(self.artist)
        response = self.client.get(reverse('soundbytes:playlist', args=['listener', self.playlist.slug]))
        self.assertContains(response, f'href="{reverse("soundbytes:profile", args=["artist"])}"')
        self.assertNotContains(response, f'href="{reverse("soundbytes:profile", args=["listener"])}"')
