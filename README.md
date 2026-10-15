# SoundByte

A Django music-sharing app for discovering artists, streaming tracks and creating playlists.

This is a personal development fork of the [original university group project](https://github.com/ryuruiyu6/WAD-project-soundbyte). The original contributors and commit history are retained. Improvements in this fork are described below; the original project specification at the end describes the intended scope, rather than a list of completed features.

## Run locally

Use **Python 3.13**. This fork uses **Django 5.2 LTS**, which [supports Python 3.13](https://docs.djangoproject.com/en/5.2/releases/5.2/#python-compatibility). The original Django 2.2 dependency did not run with the Python version specified in the old README.

On macOS/Linux:

```sh
git clone https://github.com/iluha2vuha/WAD-project-soundbyte.git
cd WAD-project-soundbyte
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python population_script.py
python manage.py runserver 127.0.0.1:8001
```

On Windows, create the environment with `py -3.13 -m venv .venv`, activate it with `.venv\Scripts\Activate.ps1` in PowerShell, then run the same `python` commands above.

Open [http://127.0.0.1:8001](http://127.0.0.1:8001). Stop the server with Ctrl+C. To run it again, activate `.venv` and run the last command. If port 8001 is busy, choose another port.

The migration command creates the local SQLite database; the population script copies the bundled sample audio and cover image into `media/`. Database files, virtual environments and generated media are ignored by Git. No private Downloads folder is needed for the sample data.

Demo accounts (local demonstration only):

| Username | Password | Role |
| --- | --- | --- |
| `fan1`, `fan2` | `pass1234` | Listener |
| `artist1`, `artist2` | `pass1234` | Artist |

Guests can browse home, search, trending, artist profiles and albums, and stream or download music. Sign in to like, comment, manage playlists or upload content. Playlist pages currently require sign-in.

## Verify changes

```sh
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
```

The 33 regression tests cover public browsing, streaming and downloads (including missing files), sign-in redirects, guest restrictions, playlist creation/ownership, search filters, upload validation, signup slug collisions, likes, comments and follows. They use an isolated test database and temporary media folder. They do not yet cover every feature or replace browser testing.

## Improvements in this fork

First pass, based on the project feedback:

- Replaced the incompatible Django dependency and documented local setup.
- Enabled guest browsing by fixing navigation and anonymous profile queries.
- Added an Explore Music entry point and kept navigation visible.
- Required sign-in for upload and album-creation pages and endpoints.
- Fixed the sign-in URL, retained the intended destination after sign-in and rejected external redirects.
- Corrected playlist option values and the playlist-creation redirect.
- Fixed missing-song/album requests to return 404 responses.
- Added 15 regression tests covering the above behaviour.

Follow-up review:

- Applied responsive Bootstrap dark layouts and removed the inactive Edit Profile button.
- Preserved search filters and fixed post-only searches returning songs.
- Validated song, post and album forms; successful song uploads return to their album.
- Handled missing audio, malformed playlist requests and colliding profile/playlist slugs.
- Restricted follow changes to POST, kept interaction redirects on-site and updated song counters atomically.

## Marker feedback backlog

The original feedback is tracked in [GitHub Issues](https://github.com/iluha2vuha/WAD-project-soundbyte/issues), with a source, priority and acceptance criteria for each item. Setup, guest browsing and the playlist failures are closed with evidence in `37d18db`. The testing issue remains open because the existing suite is a starting point, not comprehensive coverage.

- [#1 — Fix Python dependency compatibility and document local setup](https://github.com/iluha2vuha/WAD-project-soundbyte/issues/1)
- [#2 — Allow public music discovery without registration](https://github.com/iluha2vuha/WAD-project-soundbyte/issues/2)
- [#3 — Add useful profile images to the population script](https://github.com/iluha2vuha/WAD-project-soundbyte/issues/3)
- [#4 — Keep song uploads in the selected album workflow](https://github.com/iluha2vuha/WAD-project-soundbyte/issues/4)
- [#5 — Make Edit Profile functional](https://github.com/iluha2vuha/WAD-project-soundbyte/issues/5)
- [#6 — Fix adding songs to playlists and playlist creation redirects](https://github.com/iluha2vuha/WAD-project-soundbyte/issues/6)
- [#7 — Update likes and comments without reloading the page](https://github.com/iluha2vuha/WAD-project-soundbyte/issues/7)
- [#8 — Apply a simple responsive Bootstrap dark theme with green buttons](https://github.com/iluha2vuha/WAD-project-soundbyte/issues/8)
- [#9 — Move inline CSS and JavaScript out of page templates](https://github.com/iluha2vuha/WAD-project-soundbyte/issues/9)
- [#10 — Reduce repeated code in views and templates](https://github.com/iluha2vuha/WAD-project-soundbyte/issues/10)
- [#11 — Improve code clarity and comments for non-obvious behaviour](https://github.com/iluha2vuha/WAD-project-soundbyte/issues/11)
- [#12 — Document external sources and audit copied static/admin assets](https://github.com/iluha2vuha/WAD-project-soundbyte/issues/12)
- [#13 — Expand automated tests across the existing application flows](https://github.com/iluha2vuha/WAD-project-soundbyte/issues/13)
- [#14 — Review existing user journeys against the documented project scope](https://github.com/iluha2vuha/WAD-project-soundbyte/issues/14)

## Frontend theme and sources

The presentation uses [Bootswatch Darkly 5.3.8](https://bootswatch.com/darkly/), a theme for [Bootstrap 5.3.8](https://getbootstrap.com/docs/5.3/). Standard Bootstrap navigation, grid, cards and form components are customised with a charcoal background and bright green primary buttons. There are no added product features in this theme change.

Assets are served locally from `static/vendor/`; no CDN or remote font is required at runtime. The CSS font import and unavailable source-map references are omitted from the vendored builds. The system font stack is used instead. MIT notices are preserved in `static/vendor/bootswatch/LICENSE` and `static/vendor/bootstrap/LICENSE`. Application styles live in `static/css/styles.css`; the existing upload-type selector and trending filter live in `static/js/app.js`.

The server framework is [Django](https://www.djangoproject.com/). The copied `static/admin` files and bundled demo media still need a complete source/licence audit, tracked in [#12](https://github.com/iluha2vuha/WAD-project-soundbyte/issues/12). The new Bootstrap assets are credited here; this does not resolve the historical sources question on its own.

The current server settings and demo accounts are for local development. Deployment needs its own configuration and checks.

## Original group project specification

### Project Description

Our website idea is a social media platform that is for musicians to upload their music and albums to the platform and for music fans to follow artists they like, allowing them to find new artists and easily see when new songs are released. In addition to liking, commenting and downloading songs and album covers, the users should also be able to search for artists, search by different genres of music, stream music and add songs to their playlists. Musicians should be able to upload songs and images, and view how many profile views and downloads each song has.

### Project Specification

**Core Functionality:**

Users must be able to create personal accounts. 

Users will have to use accounts to upload UGC (music) or to interact with UGC (like, comment, follow other users) on the platform.

This can be done through Django, using their user authentication services.

Users must be able to upload music through their accounts, as well as interact with music they discover. This will be through listening, liking, sharing, following artists, and more.

Using SQLite, we can store related data together using related data (for example, posts will have an uploadID, artistID and the time at which it was uploaded stored in an SQL database.

Users must be able to search for music and users, using a search bar.

We may use HTML + CSS along with querying the SQL database

**Total Functionality:**

The app will utilise an algorithm to give music and artist recommendations to users.

We would likely have to use some sort of selection function, that takes into account the user’s favourite genres, followed artists, and popularity of songs, in order to determine what song to next recommend.

The app will feature a creator dashboard. This dashboard will allow artists to review the music they have uploaded on the app, with basic analytics. This may include a like to dislike ratio, a view count and average listen time.

We can use basic CSS to format a simple creator page

Users may upload basic metadata for their account. Things like profile pictures, a bio, and a username.

All we would need to do is validate inputs, to make sure people don’t upload inappropriate / malicious UGC (such as SQL injection or XSRF)


 
