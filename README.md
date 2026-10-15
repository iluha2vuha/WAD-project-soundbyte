# SoundByte

A music-sharing app built with Django, SQLite and Bootstrap. Browse and stream tracks, upload music, create playlists, follow artists and leave comments.

## Run locally

Install Git and Python 3.13, then open a terminal.

Clone the repository:

```sh
git clone https://github.com/iluha2vuha/WAD-project-soundbyte.git
cd WAD-project-soundbyte
```

Create and activate a virtual environment.

macOS / Linux:

```sh
python3.13 -m venv .venv
source .venv/bin/activate
```

Windows (Command Prompt):

```bat
py -3.13 -m venv .venv
.venv\Scripts\activate.bat
```

Install dependencies, create the database, load demo data and start the app:

```sh
python -m pip install -r requirements.txt
python manage.py migrate
python population_script.py
python manage.py runserver 127.0.0.1:8001
```

Open [http://127.0.0.1:8001](http://127.0.0.1:8001). Stop the server with Ctrl+C.

To run it again, open the project folder in a terminal, activate the virtual environment and run `python manage.py runserver 127.0.0.1:8001`. If port 8001 is busy, use 8002 and open the matching URL.

## Demo accounts

- Listeners: `fan1`, `fan2`
- Artists: `artist1`, `artist2`

Password for all demo accounts: `pass1234`. These accounts are for local use.

## Tests

```sh
python manage.py check
python manage.py test
```

## Credits

Forked from [SoundByte](https://github.com/ryuruiyu6/WAD-project-soundbyte). The interface uses [Bootswatch Darkly](https://bootswatch.com/darkly/) and [Bootstrap](https://getbootstrap.com/). Vendor licences are included in `static/vendor/`.
