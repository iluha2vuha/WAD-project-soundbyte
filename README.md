# SoundByte

A music-sharing app built with Django, SQLite and Bootstrap. Browse and stream tracks, upload music, create playlists, follow artists and leave comments.

## Run locally

Requires Python 3.13.

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

Open [http://127.0.0.1:8001](http://127.0.0.1:8001).

On Windows, use `py -3.13 -m venv .venv` and activate with `.venv\Scripts\Activate.ps1`, then run the same `python` commands.

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
