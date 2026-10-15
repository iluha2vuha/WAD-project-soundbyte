"""Regression tests for browsing, sign-in and playlist failures from the review."""
from pathlib import Path
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Album, Follow, Like, Playlist, Post, Profile, Song


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

    def test_search_keeps_query_and_filters_after_submission(self):
        response = self.client.get(reverse('soundbytes:search_page'), {
            'q': 'Test song', 'type': 'songs', 'sort': 'likes',
        })
        self.assertContains(response, 'value="Test song"')
        self.assertContains(response, 'value="songs" selected')
        self.assertContains(response, 'value="likes" selected')

    def test_post_search_does_not_return_songs_for_song_only_sort_options(self):
        post = Post.objects.create(text_content='A studio update')
        for sort_by in ['views', 'downloads']:
            with self.subTest(sort=sort_by):
                response = self.client.get(reverse('soundbytes:search_page'), {
                    'type': 'posts', 'sort': sort_by,
                })
                self.assertContains(response, post.text_content)
                self.assertNotContains(response, self.song.title)

    def test_playlist_titles_without_ascii_letters_have_working_links(self):
        self.client.force_login(self.listener)
        for title in ['🎵', '音乐', '🎵']:
            with self.subTest(title=title):
                response = self.client.post(
                    reverse('soundbytes:playlists', args=['listener']), {'title': title},
                )
                self.assertRedirects(response, reverse('soundbytes:playlists', args=['listener']))
                playlist = Playlist.objects.latest('pk')
                self.assertTrue(playlist.slug)
                self.assertEqual(self.client.get(reverse(
                    'soundbytes:playlist', args=['listener', playlist.slug],
                )).status_code, 200)

    def test_malformed_song_id_does_not_crash_add_to_playlist(self):
        self.client.force_login(self.listener)
        response = self.client.post(reverse('soundbytes:add_to_playlist'), {
            'song_id': 'not-a-number', 'playlist_slug': self.playlist.slug,
        })
        self.assertEqual(response.status_code, 404)

    def test_invalid_song_uploads_show_errors_without_saving(self):
        self.client.force_login(self.artist)
        for changes in [{}, {'album': 'invalid'}, {'title': 'x' * 51}, {'genres': ['999']}]:
            with self.subTest(changes=changes):
                data = {'content_type': 'song', 'title': 'New song', 'artist': 'artist',
                        'album': self.album.pk, **changes}
                if changes:
                    data['audio_file'] = SimpleUploadedFile('new.mp3', self.audio_bytes, content_type='audio/mpeg')
                response = self.client.post(reverse('soundbytes:upload'), data)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'soundbytes_auth/upload.html')
                self.assertTrue(response.context['song_form'].errors)
                self.assertEqual(Song.objects.count(), 1)

    def test_song_upload_redirects_to_its_album(self):
        self.client.force_login(self.artist)
        response = self.client.post(reverse('soundbytes:upload'), {
            'content_type': 'song', 'title': 'New song', 'artist': 'artist',
            'album': self.album.pk, 'tags': ' Calm, STUDIO ',
            'audio_file': SimpleUploadedFile('new.mp3', self.audio_bytes, content_type='audio/mpeg'),
        })
        self.assertRedirects(response, reverse('soundbytes:album_page', args=[self.album.pk]))
        self.assertEqual(Song.objects.get(title='New song').tags, 'calm,studio')

    def test_empty_post_upload_shows_errors_without_saving(self):
        self.client.force_login(self.artist)
        response = self.client.post(reverse('soundbytes:upload'), {
            'content_type': 'post', 'text_content': '   ',
        })
        self.assertTemplateUsed(response, 'soundbytes_auth/upload.html')
        self.assertTrue(response.context['post_form'].errors)
        self.assertFalse(Post.objects.exists())

    def test_text_post_upload_still_works(self):
        self.client.force_login(self.artist)
        response = self.client.post(reverse('soundbytes:upload'), {
            'content_type': 'post', 'text_content': 'Studio update',
        })
        self.assertRedirects(response, reverse('soundbytes:search_page'))
        self.assertEqual(Post.objects.get().text_content, 'Studio update')

    def test_image_only_post_upload_still_works(self):
        self.client.force_login(self.artist)
        image = (Path(__file__).resolve().parent.parent / 'sample_data/images/wall.png').read_bytes()
        response = self.client.post(reverse('soundbytes:upload'), {
            'content_type': 'post', 'image_file': SimpleUploadedFile('post.png', image, content_type='image/png'),
        })
        self.assertRedirects(response, reverse('soundbytes:search_page'))
        self.assertTrue(Post.objects.get().image)

    def test_invalid_post_image_shows_error_without_saving(self):
        self.client.force_login(self.artist)
        response = self.client.post(reverse('soundbytes:upload'), {
            'content_type': 'post', 'text_content': 'Update',
            'image_file': SimpleUploadedFile('fake.png', b'not an image', content_type='image/png'),
        })
        self.assertTrue(response.context['post_form'].errors)
        self.assertFalse(Post.objects.exists())

    def test_album_creation_rejects_missing_details(self):
        self.client.force_login(self.artist)
        response = self.client.post(reverse('soundbytes:create_album'), {'title': '', 'artist': ''})
        self.assertTemplateUsed(response, 'soundbytes_auth/create_album.html')
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(Album.objects.count(), 1)

    def test_album_creation_keeps_optional_cover_and_opens_upload(self):
        self.client.force_login(self.artist)
        response = self.client.post(reverse('soundbytes:create_album'), {
            'title': 'Second album', 'artist': 'artist',
        })
        self.assertRedirects(response, reverse('soundbytes:upload_page'))
        self.assertTrue(Album.objects.filter(title='Second album').exists())

    def test_like_toggle_updates_one_like_and_its_counter(self):
        self.client.force_login(self.listener)
        url = reverse('soundbytes:toggle_like', args=[self.song.pk])
        for expected in [1, 0]:
            self.client.post(url)
            self.song.refresh_from_db()
            self.assertEqual(self.song.likes.count(), expected)
            self.assertEqual(self.song.like_count, expected)

    def test_comments_save_nonempty_text(self):
        self.client.force_login(self.listener)
        url = reverse('soundbytes:add_comment', args=[self.song.pk])
        self.client.post(url, {'body': '   '})
        self.assertFalse(self.song.comments.exists())
        self.client.post(url, {'body': ' Good track '})
        self.assertEqual(self.song.comments.get().body, 'Good track')

    def test_interaction_redirects_stay_on_this_site(self):
        self.client.force_login(self.listener)
        for name in ['toggle_like', 'add_comment']:
            with self.subTest(action=name):
                url = reverse(f'soundbytes:{name}', args=[self.song.pk])
                response = self.client.post(url, {'body': 'Hello'}, HTTP_REFERER='https://example.com/')
                self.assertRedirects(response, reverse('soundbytes:search_page'))
                destination = reverse('soundbytes:profile', args=['artist'])
                response = self.client.post(url, {'body': 'Hello'}, HTTP_REFERER=destination)
                self.assertRedirects(response, destination)

    def test_follow_requires_post_and_toggles_both_relationships(self):
        self.client.force_login(self.listener)
        url = reverse('soundbytes:toggle_follow', args=['artist'])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertFalse(Follow.objects.exists())
        for expected in [1, 0]:
            self.assertRedirects(self.client.post(url), reverse('soundbytes:profile', args=['artist']))
            self.assertEqual(Follow.objects.filter(follower=self.listener, following=self.artist).count(), expected)
            self.assertEqual(self.artist.profile.followers.filter(pk=self.listener.pk).count(), expected)

    def test_missing_audio_returns_404_without_counting_a_play_or_download(self):
        self.song.audio_file.name = 'songs/missing.mp3'
        self.song.save(update_fields=['audio_file'])
        for name in ['stream_song', 'download_song']:
            with self.subTest(action=name):
                self.assertEqual(self.client.get(reverse(f'soundbytes:{name}', args=[self.song.pk])).status_code, 404)
        self.song.refresh_from_db()
        self.assertEqual(self.song.view_count, 0)
        self.assertEqual(self.song.download_count, 0)
        self.assertFalse(self.song.downloads.exists())

    def test_signup_usernames_with_matching_slugs_do_not_crash(self):
        for username in ['other.name', 'other@name', 'OTHER.NAME', '音乐', '歌手']:
            with self.subTest(username=username):
                response = self.client.post(reverse('soundbytes:signup'), {
                    'username': username, 'password': 'Test-password-2026',
                    'confirm_password': 'Test-password-2026', 'user_type': 'LISTENER',
                })
                self.assertEqual(response.status_code, 200)
                self.assertTrue(User.objects.get(username=username).profile.slug)
