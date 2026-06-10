# MSFS-GTFS

A website for viewing Maine State Ferry Service schedules using the standard General Transit Feed Specification data format.

Routes currently supported:
- Bass Harbor <=> Swan's Island

The app is a single Flask application that renders the schedule pages server-side
(Jinja templates + HTMX for live updates).

---

### GTFS Feed

The feed is hand-authored. The raw GTFS files live in `msfs_gtfs_package/` and are
zipped into `backend/Archive.zip` (a generated artifact) by the build utility:

```
python build_feed.py
```

Edit any file in `msfs_gtfs_package/`, re-run `build_feed.py`, and restart the app
to pick up the changes.

---

### Running

1. Create virtual environment: ```virtualenv venv```
2. Activate virtual environment: ```source ./venv/bin/activate```
3. Install requirements: ```pip install -r backend/requirements.txt```
4. Build the feed: ```python build_feed.py```
5. Run the app: ```cd backend && flask run```

Then open http://localhost:5000 — the landing page shows today's live schedule, and
`/schedule` shows the full weekly schedule.
