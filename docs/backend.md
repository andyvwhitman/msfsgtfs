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
  - `get_trips_for_services(service_ids)` — `Trip`s for an explicit set of `service_id`s
    (used by the by-day page to pull each day-type pattern directly).
  - `get_week_schedule(anchor_date)` — the **Mon–Sun** schedule for the week containing
    `anchor_date`, resolved by each day's **actual date** via `get_trips_on_date`, so
    `calendar_dates` exceptions (e.g. the 1st/3rd-Wednesday service) are honored. Returns a
    list of per-day dicts (`weekday`, `date`, `date_display`, `trips`, and a Wednesday `note`).
  - `get_comprehensive_schedule()` — every distinct day-type pattern in display order, with
    Wednesday split into its 1st/3rd (from `calendar_dates`) and 2nd/4th/5th (from `calendar`)
    variants. Returns `[{label, trips}, ...]`.
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
- `_summarize_trips(trips)` → time-ordered trip-summary dicts with a `display_time` added;
  shared by the weekly, by-day, and date-lookup views.
- `_use_military()` → reads the `time_format` cookie; `True` for 24-hour time. `_format_display_time`
  honors it, so the 12-/24-hour choice applies site-wide. Toggled at `/prefs/time-format`
  (sets a 1-year cookie and redirects back, so the preference persists across sessions).
- `_format_countdown(departure_time, now_seconds)` → time until a departure as `"in Hh MMm"`
  / `"in Mm"`; shown beside the Next Departure times and recomputed every render.
- `_wednesday_note(day_date)` → a short note on which Wednesday schedule a date runs (ordinal
  Wednesday-of-month + whether the `calendar_dates`-added 1st/3rd service or the regular
  2nd/4th/5th service is active).

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

### `get_week_schedule(anchor_date)` (weekly page)

Resolves each day of the current week by its real date, so Wednesday correctly shows the
1st/3rd vs 2nd/4th/5th variant (the earlier `get_weekly_schedule` built only from
`calendar.txt` flags and so always showed the 2nd/4th/5th Wednesday). The `/schedule` route
anchors on `_current_datetime().date()` (honoring `?now=`), builds a `week_label` date range,
and passes port abbreviations via `_abbreviate`.

### `_build_date_context(date_str)` (date-picker page)

Builds the plain per-port departure lists for one date — **no** past/active/next status, so
the card is identical whether or not the date is today. Adds a Wednesday `note` when relevant.

## Routes

| Route | Handler | Renders |
|---|---|---|
| `/` | `index()` | `index.html` — full home page |
| `/schedule/fragment` | `schedule_fragment()` | `_schedule.html` — the HTMX-polled fragment |
| `/schedule` | `schedule()` | `schedule.html` — current-week calendar |
| `/by-day` | `by_day()` | `byday.html` — every day-type pattern, stacked |
| `/date` | `date_lookup()` | `datepick.html` — date picker (prefilled to today) |
| `/date/fragment` | `date_fragment()` | `_date_card.html` — one date's plain card (HTMX) |
| `/map` | `vessel_map()` | `map.html` — VesselFinder live AIS map |
| `/about` | `about()` | `about.html` — About + Buy Me a Coffee (footer-linked) |
| `/prefs/time-format` | `toggle_time_format()` | flips the 12-/24-hour cookie, redirects back |

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
