# MSFS-GTFS

A website for viewing Maine State Ferry Service schedules using the standard General Transit
Feed Specification (GTFS) data format. Currently supports Bass Harbor ⇄ Swan's Island.

The app is a single Flask application that renders its pages server-side (Jinja templates +
HTMX for live updates) from a hand-authored GTFS feed.

## Quick start

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r backend/requirements.txt
python build_feed.py            # zip msfs_gtfs_package/ -> backend/Archive.zip
cd backend && flask run         # open http://localhost:5000
```

To edit the schedule: change a file in `msfs_gtfs_package/`, re-run `python build_feed.py`,
and restart the app (the feed is read once at startup).

## Documentation

Full documentation lives in [`docs/`](docs/README.md):

- [Overview](docs/overview.md) — what it does, plus dev & production install/deploy/run
- [Architecture](docs/architecture.md) — system topology and design rationale
- [Backend](docs/backend.md) — Flask app, GTFS domain model, schedule logic
- [Frontend](docs/frontend.md) — Jinja templates, HTMX, CSS design system
- [Code Style](docs/code-style.md) — docstring/comment conventions
