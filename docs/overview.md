# Overview

## What it is

**MSFS-GTFS** is a web app that displays Maine State Ferry Service schedules for the
Bass Harbor ⇄ Swan's Island route. The schedule data is provided in the standard
[GTFS](https://gtfs.org/) (General Transit Feed Specification) format. Because the State
ferry does not publish a GTFS feed, the feed is **hand-authored** in this repo and bundled
into the app.

## What it does

- **Home page (`/`)** — today's live schedule: the next departure, a "trip in progress"
  graphic for any sailing currently underway, and the full list of today's departures from
  each port, color-coded by status (past / upcoming / in-progress / next). The page refreshes
  itself every 60 seconds.
- **Weekly schedule (`/schedule`)** — the **current week's** Monday–Sunday timetable as a
  calendar (a column per day split into the two ports), horizontal on desktop and stacked on
  phones. The Wednesday column notes which variant (1st/3rd vs 2nd/4th/5th) is running.
- **Schedule by day (`/by-day`)** — every distinct day-type pattern stacked vertically, with
  the two Wednesday schedules listed separately.
- **Find a date (`/date`)** — pick any date to see that day's departures (a plain list, no
  live highlighting).
- **Live map (`/map`)** — a VesselFinder embedded AIS map framed on the two terminals,
  showing live positions of all vessels in the area (staging for future ferry AIS tracking).

## How it works (high level)

The raw GTFS text files live in `msfs_gtfs_package/`. A small script (`build_feed.py`) zips
them into `backend/Archive.zip`. The Flask app reads that zip into memory once at startup
(via the `gtfs_kit` library) and renders pages from it with Jinja templates; HTMX handles
the live refresh. There is no database and no external service at runtime. See
[Architecture](architecture.md) for the full picture.

---

## Download

```bash
git clone <your-repo-url> msfsgtfs
cd msfsgtfs
```

## Development

Requirements: Python 3.11+ (the repo is developed on 3.13).

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Build the GTFS feed (zips msfs_gtfs_package/ -> backend/Archive.zip)
python build_feed.py

# 4. Run the app (development is the default environment)
cd backend
flask run
```

Open http://localhost:5000 — the home page is `/`, the weekly schedule is `/schedule`.

**Editing the schedule data:** edit the files in `msfs_gtfs_package/`, re-run
`python build_feed.py`, and restart the server (the feed is read once at startup).

**Developer tooling:** in development (`MSFSGTFS_ENV` unset or `development`), the home page
shows a debug time picker and accepts a `?now=` query param so you can view the schedule
as if it were any date/time — e.g. `http://localhost:5000/?now=2026-06-12T09:00`. This is
controlled by the `DEV_MODE` flag in `backend/config.py` and is independent of how Flask is
launched. See [Backend](backend.md#dev-only-time-override) for details.

## Production

The app runs under [gunicorn](https://gunicorn.org/) (already in `requirements.txt`) using
the `backend/wsgi.py` entrypoint, which exposes the Flask `app`.

```bash
# From the repo root, with the venv active and the feed built:
python build_feed.py                 # ensure backend/Archive.zip exists
cd backend
export MSFSGTFS_ENV=production        # disables dev-only tooling (?now=, debug bar)
gunicorn wsgi:app                     # add --bind 0.0.0.0:8000 --workers N as needed
```

Notes:
- Set `MSFSGTFS_ENV=production` so the dev time-override tools are disabled.
- `backend/Archive.zip` is a generated artifact (git-ignored) — build it as part of
  deployment.
- Put gunicorn behind a reverse proxy (nginx/Caddy) for TLS and static-file serving in a
  real deployment.

## Optional: serve these docs as a website

The docs are plain Markdown viewable in Obsidian. To browse them as a site instead:

```bash
pip install mkdocs-material
mkdocs serve        # uses mkdocs.yml at the repo root; open http://localhost:8000
```

MkDocs is **not** a project dependency — it's only needed if you want the docs website.
