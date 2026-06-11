# Backend

The backend is a single Flask application: `backend/main.py`, configured by
`backend/config.py`, served in production via `backend/wsgi.py`. It depends on
[`gtfs_kit`](https://mrcagney.github.io/gtfs_kit_docs/) (built on pandas/geopandas) to read
the GTFS feed.

## Bootstrap

At import time `main.py`:

1. Loads config via `app.config.from_pyfile('config.py')`.
2. Resolves the feed path relative to the `backend/` directory and reads the feed once:
   ```python
   feed_path = Path(__file__).parent / app.config.get('GTFS_FEED_PATH', 'Archive.zip')
   feed = gk.read_feed(feed_path, dist_units='mi')
   ```
   `feed` is a module-level global reused by every request (see
   [Architecture](architecture.md#why-its-built-this-way)).

### Configuration (`backend/config.py`)

- `ENV` / `DEV_MODE` — derived from the `MSFSGTFS_ENV` environment variable (`development`
  by default). `DEV_MODE` gates all developer tooling.
- `DEBUG` — set for Flask's own use, but **not** used to gate features (the `flask run` CLI
  overrides it).
- `GTFS_FEED_PATH` — feed filename (`Archive.zip`).
- `ROUTE_ID`, `STOP_A_ID`/`STOP_A_NAME`, `STOP_B_ID`/`STOP_B_NAME` — the single route and its
  two terminals.

## Domain model

Thin wrappers turn `gtfs_kit`'s DataFrames into objects the templates can use:

- **`Route`** — one GTFS route. Key methods:
  - `get_trips_on_date(date)` — `Trip`s scheduled on a `YYYYMMDD` date (honors
    `calendar.txt` + `calendar_dates.txt`).
  - `get_trips_today()` — convenience wrapper for the current date.
  - `get_weekly_schedule()` — the recurring **Mon–Sun** pattern as
    `{weekday: [trip summary, ...]}`, built from `calendar.txt` weekday flags rather than
    per-date lookups so it's well-defined regardless of the current date.
- **`Trip`** — one sailing. Exposes `originating_stop`/`destination_stop` (as `Stop`s),
  `departure_time`/`arrival_time` (GTFS `"HH:MM:SS"`), and `get_trip_summary()` which returns
  a plain dict (the shape the templates and schedule logic consume).
- **`Stop`** — one terminal; `get_stop_summary()` returns id/name/desc/lat/lon.
- **`StopTime`** — a single stop on a trip (arrival/departure/sequence).

## Time helpers

GTFS times are `"HH:MM:SS"` strings and may exceed `24:00:00` for post-midnight service.

- `_parse_gtfs_time(t)` → a `datetime.time` (wraps hours ≥ 24 to the same day).
- `_format_display_time(t)` → a human label like `"6:45 AM"`.
- `_gtfs_seconds(t)` → seconds since midnight (used for arithmetic and sorting).
- `_trip_progress_pct(dep, arr, now_seconds)` → percent of a voyage elapsed (0–100, clamped).
  A **guesstimate** from elapsed/expected duration — a placeholder until GPS/AIS data is wired
  in for a true position-based estimate.
- `_abbreviate(name)` → initials, e.g. `"Swan's Island"` → `"SI"` (used for weekly column
  headers).

## Schedule logic

### `_build_schedule_context()` (home page)

Builds the context for `/` and the `/schedule/fragment` poll:

1. Resolves "now" via `_current_datetime()` (honoring the dev `?now=` override).
2. Gets today's trips (`route.get_trips_on_date(now.date)`), each as a summary dict.
3. Classifies each trip by comparing now against its departure/arrival:
   - **past** — already arrived
   - **active** — departed but not yet arrived (in progress)
   - **future** — not yet departed
4. Splits trips into the two ports (`stop_a_trips`, `stop_b_trips`).
5. Flags **the single soonest** upcoming departure across both ports with `is_next` (this is
   the one highlighted green — not the next per port).
6. Builds `active_trips`: for each in-progress sailing, the from/to port names, display times,
   and `progress_pct` for the in-progress graphic.
7. Adds the dev fields `dev_mode`, `now_qs`, `now_input` (see below).

The four trip states map to colors in the UI — see [Frontend](frontend.md#trip-status-colors).

### `get_weekly_schedule()` (weekly page)

For each weekday, selects the `service_id`s whose `calendar.txt` flag is set, gathers this
route's trips for those services, time-orders them, and attaches a `display_time`. The
`/schedule` route also passes port abbreviations via `_abbreviate`.

## Routes

| Route | Handler | Renders |
|---|---|---|
| `/` | `index()` | `index.html` — full home page |
| `/schedule/fragment` | `schedule_fragment()` | `_schedule.html` — the HTMX-polled fragment |
| `/schedule` | `schedule()` | `schedule.html` — weekly calendar |

## Dev-only time override

`_current_datetime()` returns the real wall clock **unless** `DEV_MODE` is on and a `now`
query parameter is present, in which case it parses that value (an ISO datetime/date, or a
bare `"HH:MM[:SS]"` combined with today) and returns it. This drives:

- **which day's** trips are shown (the override's date), and
- **past/active/future** classification and progress (the override's time).

`_build_schedule_context` also returns `now_qs` (e.g. `?now=...`) which the fragment's
`hx-get` uses so the override survives the 60s auto-refresh, and `now_input` for the picker.
When `MSFSGTFS_ENV=production`, `DEV_MODE` is false: the param is ignored and the debug bar is
hidden. This is intentionally decoupled from Flask's `DEBUG` — see
[Architecture](architecture.md#why-its-built-this-way).
