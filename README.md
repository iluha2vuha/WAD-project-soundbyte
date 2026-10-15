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

The regression tests cover public browsing, streaming and downloads, sign-in redirects, guest restrictions and playlist creation/ownership. They use an isolated test database and temporary media folder. They do not yet cover every feature or replace browser testing.

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

Remaining work from the feedback:

- Make profile editing functional.
- Validate uploads and return users to the relevant album with clear success/error messages.
- Update likes and comments without reloading the page.
- Redesign spacing, controls, navigation and layouts for desktop and mobile.
- Add profile images to the sample data.
- Consolidate duplicate view/template code and move remaining inline CSS/JavaScript into static files.
- Audit copied `static/admin` assets and document third-party sources and media credits.
- Expand tests to uploads, profile editing, interactions and browser journeys.

The current server settings and demo accounts are for local development. Deployment needs its own configuration and checks; the frontend redesign is still pending.

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


 
