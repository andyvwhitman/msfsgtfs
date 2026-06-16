# Frontend

The frontend is **server-rendered**: Jinja templates produce HTML on each request, with
[HTMX](https://htmx.org/) for live updates and a single CSS file for styling. There is no
JavaScript build step and no client-side framework.

## Templates (`backend/templates/`)

| Template | Role |
|---|---|
| `base.html` | Page shell: `<head>`, the site nav, and the `{% block content %}` every page fills. Includes the HTMX library via CDN and sets a per-page `{% block title %}`. |
| `index.html` | Home page. Header + `{% include "_schedule.html" %}`. |
| `_schedule.html` | The live schedule **fragment**: next departure, in-progress voyage, today's trips, and (in dev) the debug bar. Rendered both inside the home page and standalone at `/schedule/fragment`. |
| `schedule.html` | Weekly page: the 7-day calendar for the **current week** (real dates). |
| `byday.html` | By-day page: every day-type pattern stacked vertically (Wednesday split into its two variants). |
| `datepick.html` | Date-picker page: a `type="date"` input whose change swaps in that date's card via HTMX. |
| `_date_card.html` | The plain per-date departure card (HTMX target of the date picker); no live status colors. |
| `map.html` | Live map page: the VesselFinder embedded AIS map. |
| `_macros.html` | The `day_block(trips, a_abbr, b_abbr)` macro — the two-port departure grid reused by the weekly and by-day pages. |

The context variables these consume are produced by the backend — see
[Backend → Schedule logic](backend.md#schedule-logic).

## Live updates with HTMX

The fragment refreshes itself without a full page reload:

```html
<div id="schedule-live"
     hx-get="/schedule/fragment{{ now_qs }}"
     hx-trigger="every 60s"
     hx-swap="outerHTML">
```

- `hx-trigger="every 60s"` polls the server once a minute.
- `hx-get` fetches `/schedule/fragment`; `hx-swap="outerHTML"` replaces the element with the
  fresh HTML. This advances the "next departure" and the in-progress progress bar over time.
- `{{ now_qs }}` carries the dev `?now=` override through the poll so a simulated time doesn't
  snap back to real time on refresh (see [Backend](backend.md#dev-only-time-override)).

## Design system (`backend/static/style.css`)

A light, card-based layout in a subtle **nautical (seafoam teal)** theme. All colors are
defined once as CSS custom properties in `:root` and referenced via `var(--…)`, so the
palette is tunable in one place:

| Variable | Role |
|---|---|
| `--bg` | page background (pale teal sea-mist) |
| `--surface` | card background (white) |
| `--ink` / `--muted` / `--faint` | primary / secondary / tertiary text |
| `--accent` | teal — active nav, links |
| `--next` | sea green — the next departure |
| `--live` | steel-teal — in-progress trips **and** the voyage progress bar |
| `--border` | hairlines, dividers, empty marks |

Notable pieces:

### Trip status colors

The home schedule color-codes each departure by the status the backend assigns:

| Status | Meaning | Style |
|---|---|---|
| `past` | already arrived | greyed / faded |
| `future` | upcoming | dark text |
| `active` | in progress now | **steel-teal** (`--live`), italic |
| `next` | the single soonest departure | **sea green** (`--next`), bold |

### In-progress voyage graphic

When a sailing is underway, `_schedule.html` renders a `.voyage` block: the two port names at
the ends, a `.progress-track` rail with a `.progress-fill` in the live color (`--live`) and a
ferry marker (`.ferry-dot`) positioned by inline `left: {{ progress_pct }}%`. The card always
renders; with no active sailing it shows "No trip in progress."

### Weekly calendar (responsive)

`schedule.html` uses the `.week-grid` (7 day columns) for the current week, each column headed
by the weekday name and its date. Each day splits into two port sub-columns headed by
abbreviations (`SI` / `BH`). The Wednesday column carries a `.wed-note` saying which variant
is running that week (e.g. *"3rd Wednesday — 1st & 3rd schedule"*). A `max-width: 720px` media
query collapses the grid to a **single column** so days stack and the page scrolls vertically
on phones; on wider screens it stays horizontal.

### By-day and date-picker pages

`byday.html` stacks one `.day-card` per day-type pattern, each using the shared `day_block`
macro. `datepick.html` holds a `type="date"` input with `hx-trigger="change"` that swaps the
plain `_date_card.html` (no status colors) into `#date-result`.

### Live map

`map.html` embeds VesselFinder's free AIS map via its two-`<script>` snippet (config vars +
`aismap.js`) inside a `.map-container`. It needs no account or API key and shows live
positions of all vessels in view — staging for future ferry-specific AIS tracking.

### Footer

`base.html` renders a footer on every page: a "Built by Andy Whitman" credit with copyright
year and an About link, plus a subtle **12-hour / 24-hour** toggle. The toggle links to
`/prefs/time-format`, which sets a year-long `time_format` cookie and redirects back, so the
choice persists across sessions and re-renders all times site-wide.

### Next-departure countdown

The Next Departure card shows a small `(in Hh MMm)` countdown beside each time, recomputed on
every render (and on the 60s HTMX refresh).

### Background

The page background is a pale-teal base plus a faint tiled nautical-chart bathymetry SVG
(`backend/static/bathymetry.svg`) — islands, depth contours, and shelf lines for subtle ocean
color behind the cards.

### Debug bar (dev only)

When `dev_mode` is true, the fragment renders a small `.debug-bar` form with a
`datetime-local` picker that submits a `now` value to `/`, plus a reset link. Hidden in
production.
