# MUST KOOSEN — Backend (Django)

Django + DRF backend for the MUST KOOSEN school site.

## Requirements
- Python 3.10+
- PostgreSQL 13+
- Tesseract OCR (only needed for the PDF/Word import feature — see `TESSERACT_INSTALL.md`)

## Local setup

```bash
# 1. clone & enter the project
git clone https://github.com/bilguun2026/kosenBack.git
cd kosenBack

# 2. virtualenv
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. dependencies
pip install -r requirements.txt

# 4. env file — copy and edit
cp .env.example .env
# then open .env and set SECRET_KEY, DB_*, ALLOWED_HOSTS, etc.

# 5. database (PostgreSQL must already be running and DB created)
python manage.py migrate
python manage.py createsuperuser

# 6. run
python manage.py runserver 0.0.0.0:8000
```

The API is now at `http://localhost:8000/api/` and admin at `http://localhost:8000/admin/`.

## Production deployment checklist

1. Set `DEBUG=False` in `.env`.
2. Generate a strong `SECRET_KEY` (e.g. `python -c "import secrets; print(secrets.token_urlsafe(50))"`).
3. Set `ALLOWED_HOSTS` to your real domain/IP.
4. Run `python manage.py collectstatic --noinput` (creates `staticfiles/`).
5. Run `python manage.py migrate` — **all migrations are tracked in git**, no need to `makemigrations` on the server.
6. Serve via gunicorn/uwsgi behind nginx; have nginx serve `/media/` and `/static/` directly.
7. Make sure `media/` is on persistent storage (volume mount, S3, etc.) — the folder is gitignored except for a placeholder `.gitkeep`.

## Endpoints

- `/api/` — DRF endpoints (see `rest/urls.py`)
- `/admin/` — Django admin (Jazzmin themed)
- `/ckeditor5/` — rich-text editor uploads
- `/swagger/` and `/redoc/` — API docs
- `/media/...` — uploaded files (served by Django when DEBUG=True, by nginx in prod)
