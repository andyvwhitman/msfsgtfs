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
| `schedule.html` | Weekly page: the horizontal 7-day calendar. |

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

A light, card-based layout. Notable pieces:

### Trip status colors

The home schedule color-codes each departure by the status the backend assigns:

| Status | Meaning | Style |
|---|---|---|
| `past` | already arrived | greyed / faded |
| `future` | upcoming | dark text |
| `active` | in progress now | **blue**, italic |
| `next` | the single soonest departure | **green**, bold |

### In-progress voyage graphic

When a sailing is underway, `_schedule.html` renders a `.voyage` block: the two port names at
the ends, a `.progress-track` rail with a green `.progress-fill` and a ferry marker
(`.ferry-dot`) positioned by inline `left: {{ progress_pct }}%`. The card always renders;
with no active sailing it shows "No trip in progress."

### Weekly calendar

`schedule.html` uses a horizontal `.week-grid` (7 day columns; scrolls horizontally on
narrow screens). Each day splits into two port sub-columns headed by abbreviations
(`SI` / `BH`) with a legend; times are kept on one line via `white-space: nowrap`.

### Debug bar (dev only)

When `dev_mode` is true, the fragment renders a small `.debug-bar` form with a
`datetime-local` picker that submits a `now` value to `/`, plus a reset link. Hidden in
production.
