"""Flask app for the Maine State Ferry Service schedule.

Serves three server-rendered pages backed by a GTFS feed read into memory at
startup: the live "today" schedule (``/``), its 60s HTMX refresh fragment
(``/schedule/fragment``), and the recurring weekly calendar (``/schedule``).
The thin Route/Trip/Stop/StopTime wrappers below adapt gtfs_kit's DataFrames
into plain objects the templates can consume.
"""
import math
from pathlib import Path
from urllib.parse import quote

from datetime import datetime, date, timedelta

import gtfs_kit as gk

from flask import Flask, render_template, request, redirect

app = Flask(__name__)
app.config.from_pyfile('config.py')

# The GTFS feed is small and read-only, so it is loaded once at import and held
# in memory for the life of the process. Rebuild Archive.zip with build_feed.py.
feed_path = Path(__file__).parent / app.config.get('GTFS_FEED_PATH', 'Archive.zip')
print(feed_path)
feed = gk.read_feed(feed_path, dist_units='mi')

WEEKDAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

@app.context_processor
def inject_globals():
    """Expose values available to every template (footer year + time/map prefs)."""
    return {
        'current_year': datetime.now().year,
        'military_time': _use_military(),
        'map_provider': _map_provider(),
    }

class Route():
    """A single GTFS route and the trips that run on it."""

    def __init__(self, feed, route_id):
        self.feed = feed
        self.route_id = route_id

        try:
            route = self.feed.routes[self.feed.routes['route_id'] == self.route_id].iloc[0]
        except:
            raise KeyError("Route not found")

        self.route_type = route.route_type
        self.agency_id = route.agency_id
        self.route_short_name = route.route_short_name
        self.route_long_name = route.route_long_name
        self.route_desc = route.route_desc
        self.route_url = route.route_url
        self.route_color = route.route_color
        self.route_text_color = route.route_text_color
        self.route_sort_order = route.route_sort_order
        self.continuous_pickup = route.continuous_pickup
        self.continuous_drop_off = route.continuous_drop_off
        self.network_id = route.network_id

    def get_trips_today(self):
        """Return this route's Trip objects scheduled for the current date."""
        date = datetime.now().strftime("%Y%m%d")
        return self.get_trips_on_date(date)

    def get_trips_on_date(self, date):
        """Return this route's Trip objects scheduled on a date (YYYYMMDD)."""
        all_trips = self.feed.get_trips(date=date)
        route_trips = all_trips[all_trips["route_id"] == self.route_id]

        return [Trip(self.feed, t.trip_id) for t in route_trips.itertuples()]

    def get_trips_for_services(self, service_ids):
        """Return this route's Trip objects whose service_id is in service_ids."""
        ids = {str(s) for s in service_ids}
        route_trips = self.feed.trips[
            (self.feed.trips['route_id'] == self.route_id)
            & (self.feed.trips['service_id'].astype(str).isin(ids))
        ]
        return [Trip(self.feed, t.trip_id) for t in route_trips.itertuples()]

    def get_week_schedule(self, anchor_date):
        """Return the Mon-Sun schedule for the week containing anchor_date.

        Each day is resolved by its actual date via get_trips_on_date, so
        calendar_dates exceptions (e.g. the 1st/3rd-Wednesday service) are
        honored — unlike a pattern built from weekday flags alone. Returns a
        list of per-day dicts (weekday name, date, time-ordered trips, and for
        Wednesday a note on which variant is running) in Mon-Sun order.
        """
        monday = anchor_date - timedelta(days=anchor_date.weekday())
        week = []
        for offset, name in enumerate(WEEKDAYS):
            day_date = monday + timedelta(days=offset)
            day = {
                'weekday': name.capitalize(),
                'date': day_date,
                'date_display': day_date.strftime('%b %-d'),
                'trips': _summarize_trips(self.get_trips_on_date(day_date.strftime('%Y%m%d'))),
            }
            if name == 'wednesday':
                day['note'] = _wednesday_note(day_date)
            week.append(day)
        return week

    def get_comprehensive_schedule(self):
        """Return every distinct day-type pattern in display order.

        Mon/Tue/Fri/Sat share a single service in summer but are listed
        separately for clarity; Wednesday is split into its 1st/3rd and
        2nd/4th/5th variants, which live in calendar_dates and calendar
        respectively. Service ids are derived from the feed, not hardcoded.
        """
        calendar = self.feed.calendar
        calendar_dates = self.feed.calendar_dates

        def services_for_weekday(day):
            return calendar[calendar[day].astype(int) == 1]['service_id'].astype(str).tolist()

        wed_regular = services_for_weekday('wednesday')  # 2nd/4th/5th Wed
        wed_exception = (
            calendar_dates[calendar_dates['exception_type'].astype(int) == 1]['service_id']
            .astype(str).unique().tolist()  # 1st/3rd Wed (added via calendar_dates)
        )

        rows = [
            ('Monday', services_for_weekday('monday')),
            ('Tuesday', services_for_weekday('tuesday')),
            ('Wednesday (1st & 3rd)', wed_exception),
            ('Wednesday (2nd, 4th & 5th)', wed_regular),
            ('Thursday', services_for_weekday('thursday')),
            ('Friday', services_for_weekday('friday')),
            ('Saturday', services_for_weekday('saturday')),
            ('Sunday', services_for_weekday('sunday')),
        ]
        return [
            {'label': label, 'trips': _summarize_trips(self.get_trips_for_services(svc))}
            for label, svc in rows
        ]

class Trip():
    """A single GTFS trip: one scheduled sailing with its ordered stop times."""

    def __init__(self, feed, trip_id):
        self.feed = feed
        self.trip_id = trip_id

        try:
            trip = self.feed.trips[self.feed.trips['trip_id'] == self.trip_id].iloc[0]
        except:
            raise KeyError("Trip not found")

        self.route_id = trip.route_id
        self.service_id = trip.service_id
        self.trip_headsign = trip.trip_headsign
        self.trip_short_name = trip.trip_short_name
        self.direction_id = int(trip.direction_id)
        self.block_id = trip.block_id
        self.shape_id = trip.shape_id
        self.wheelchair_accessible = trip.wheelchair_accessible
        self.bikes_allowed = trip.bikes_allowed

        stop_times = self.feed.stop_times[self.feed.stop_times['trip_id'] == self.trip_id]
        self.stop_times =  [StopTime(self.feed, t.trip_id, t.arrival_time, t.departure_time, t.stop_sequence, t.stop_id) for t in stop_times.itertuples()]

    @property
    def originating_stop(self):
        """The Stop where this trip begins (first stop time)."""
        return Stop(self.feed, self.stop_times[0].stop_id)

    @property
    def destination_stop(self):
        """The Stop where this trip ends (last stop time)."""
        return Stop(self.feed, self.stop_times[-1].stop_id)

    @property
    def departure_time(self):
        """GTFS departure time from the originating stop ("HH:MM:SS")."""
        return self.stop_times[0].departure_time

    @property
    def arrival_time(self):
        """GTFS arrival time at the destination stop ("HH:MM:SS")."""
        return self.stop_times[-1].arrival_time

    def get_trip_summary(self):
        """Return a plain-dict summary of this trip for templates/JSON."""
        trip_summary = {}

        trip_summary['trip_id'] = self.trip_id
        trip_summary['route_id'] = self.route_id
        trip_summary['trip_headsign'] = self.trip_headsign
        trip_summary['direction_id'] = self.direction_id
        trip_summary['originating_stop'] = self.originating_stop.get_stop_summary()
        trip_summary['destination_stop'] = self.destination_stop.get_stop_summary()
        trip_summary['departure_time'] = self.departure_time
        trip_summary['arrival_time'] = self.arrival_time

        return trip_summary

    def __repr__(self):
        return f"{self.trip_id}"

class Stop():
    """A single GTFS stop (a ferry terminal)."""

    def __init__(self, feed, stop_id):
        self.feed = feed
        self.stop_id = stop_id

        try:
            stop = self.feed.stops[self.feed.stops['stop_id'] == self.stop_id].iloc[0]
        except:
            raise KeyError("Stop not found")

        self.stop_code = stop.stop_code
        self.stop_name = stop.stop_name
        self.tts_stop_name = stop.tts_stop_name
        self.stop_desc = stop.stop_desc
        self.stop_lat = float(stop.stop_lat)
        self.stop_lon = float(stop.stop_lon)
        self.zone_id = stop.zone_id
        self.stop_url = stop.stop_url
        self.location_type = stop.location_type
        self.parent_station = stop.parent_station
        self.stop_timezone = stop.stop_timezone
        self.wheelchair_boarding = stop.wheelchair_boarding
        self.level_id = stop.level_id
        self.platform_code = stop.platform_code

    def get_stop_summary(self):
        """Return a plain-dict summary of this stop for templates/JSON."""
        stop_summary = {}

        stop_summary['stop_id'] = self.stop_id
        stop_summary['stop_name'] = self.stop_name
        stop_summary['stop_desc'] = self.stop_desc
        stop_summary['stop_lat'] = self.stop_lat
        stop_summary['stop_lon'] = self.stop_lon

        return stop_summary

class StopTime():
    """One stop on a trip: its arrival/departure times and sequence position."""

    def __init__(self, feed, trip_id, arrival_time, departure_time, stop_sequence, stop_id):
        self.feed = feed
        self.trip = trip_id
        self.arrival_time = arrival_time
        self.departure_time = departure_time
        self.stop_sequence = stop_sequence
        self.stop_id = stop_id

    def __repr__(self):
        return f"Departing {self.stop_id} at {self.departure_time}"


def _parse_gtfs_time(t):
    """Parse a GTFS "HH:MM:SS" string into a time, wrapping hours >= 24 to same-day."""
    h, m, s = map(int, t.split(':'))
    if h >= 24:
        h -= 24
    return datetime.now().replace(hour=h, minute=m, second=s, microsecond=0).time()

def _use_military():
    """True if the visitor opted into 24-hour (military) time via the cookie."""
    return request.cookies.get('time_format') == '24'

def _map_provider():
    """Return the visitor's saved maps provider ('apple'/'google'), or None if unset."""
    provider = request.cookies.get('map_provider')
    return provider if provider in ('apple', 'google') else None

def _format_display_time(t):
    """Format a GTFS "HH:MM:SS" for display, honoring the 12-/24-hour cookie.

    Returns e.g. "6:45 AM" by default, or "06:45" when the visitor has chosen
    24-hour time (persisted across sessions via the time_format cookie).
    """
    h, m, _ = map(int, t.split(':'))
    if h >= 24:
        h -= 24
    if _use_military():
        return f"{h:02d}:{m:02d}"
    period = 'AM' if h < 12 else 'PM'
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {period}"

def _format_countdown(departure_time, now_seconds):
    """Return the time until a departure as "in Hh MMm" / "in Mm", or None if passed."""
    delta = _gtfs_seconds(departure_time) - now_seconds
    if delta < 0:
        return None
    minutes = math.ceil(delta / 60)
    hours, mins = divmod(minutes, 60)
    return f"in {hours}h {mins:02d}m" if hours else f"in {mins}m"

def _abbreviate(name):
    """Return the initials of each word, e.g. "Swan's Island" -> "SI"."""
    letters = [w[0].upper() for w in name.split() if w[:1].isalpha()]
    return ''.join(letters) or name[:2].upper()

def _current_datetime():
    """Return the current datetime, honoring a dev-only ?now= override.

    In DEV_MODE a ?now= query param lets you view the schedule as if it were
    another date/time; otherwise this is the real wall clock. Accepts an ISO
    datetime/date or a bare "HH:MM[:SS]" (combined with today).
    """
    if app.config.get('DEV_MODE'):
        override = request.args.get('now')
        if override:
            try:
                return datetime.fromisoformat(override)
            except ValueError:
                pass
            try:
                h, m, *rest = map(int, override.split(':'))
                s = rest[0] if rest else 0
                return datetime.now().replace(hour=h, minute=m, second=s, microsecond=0)
            except (ValueError, TypeError):
                pass
    return datetime.now()

def _gtfs_seconds(t):
    """Return seconds since midnight for a GTFS "HH:MM:SS" (keeps hours >= 24)."""
    h, m, s = map(int, t.split(':'))
    return h * 3600 + m * 60 + s

def _trip_progress_pct(departure_time, arrival_time, now_seconds):
    """Return percent of a voyage elapsed (0-100), clamped.

    A guesstimate from elapsed/expected duration, given the GTFS departure and
    arrival "HH:MM:SS" times and the current seconds-since-midnight. This is a
    stand-in until GPS/AIS data provides a true position-based estimate.
    """
    dep_s = _gtfs_seconds(departure_time)
    arr_s = _gtfs_seconds(arrival_time)
    if arr_s <= dep_s:
        return 100.0
    pct = (now_seconds - dep_s) / (arr_s - dep_s) * 100
    return max(0.0, min(100.0, pct))

def _maps_links(stop_id, label):
    """Return Apple/Google Maps URLs pinned to a terminal's coordinates.

    Uses the stop's exact GTFS lat/lon with the display name as the pin label,
    so both providers land precisely on the terminal regardless of how its
    street address geocodes. Consumed by the next-departure "open in maps" modal.
    """
    stop = Stop(feed, stop_id)
    ll = f"{stop.stop_lat},{stop.stop_lon}"
    return {
        'apple': f"https://maps.apple.com/?q={quote(label)}&ll={ll}",
        'google': f"https://www.google.com/maps/search/?api=1&query={ll}",
    }

def _summarize_trips(trips):
    """Return time-sorted trip summaries with a display_time added.

    Shared by the weekly, by-day, and date-lookup views, which all render the
    same two-port departure layout from a list of Trip objects.
    """
    summaries = [t.get_trip_summary() for t in trips]
    summaries.sort(key=lambda s: s['departure_time'])
    for s in summaries:
        s['display_time'] = _format_display_time(s['departure_time'])
    return summaries

def _wednesday_note(day_date):
    """Return a short note on which Wednesday schedule applies to a date.

    Combines the ordinal Wednesday-of-month with whether the date runs the
    calendar_dates-added 1st/3rd service or the regular 2nd/4th/5th service,
    so the label reflects the feed rather than a hardcoded rule.
    """
    ordinal = (day_date.day - 1) // 7 + 1
    suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(ordinal, 'th')
    date_str = day_date.strftime('%Y%m%d')
    active = set(feed.get_trips(date=date_str)['service_id'].astype(str))
    exception_services = set(
        feed.calendar_dates.loc[
            feed.calendar_dates['exception_type'].astype(int) == 1, 'service_id'
        ].astype(str)
    )
    variant = '1st & 3rd schedule' if active & exception_services else '2nd, 4th & 5th schedule'
    return f"{ordinal}{suffix} Wednesday — {variant}"

def _build_date_context(date_str):
    """Build context for the date-lookup card: plain per-port lists for a date.

    Deliberately carries no live status (past/next/in-progress) — the list is
    identical regardless of whether the date is today.
    """
    stop_a_id = app.config.get('STOP_A_ID', '1001')
    stop_b_id = app.config.get('STOP_B_ID', '1002')

    route = Route(feed, app.config.get('ROUTE_ID', '1000'))
    trips = _summarize_trips(route.get_trips_on_date(date_str))
    stop_a_trips = [t for t in trips if t['originating_stop']['stop_id'] == stop_a_id]
    stop_b_trips = [t for t in trips if t['originating_stop']['stop_id'] == stop_b_id]

    day_date = datetime.strptime(date_str, '%Y%m%d').date()
    context = {
        'stop_a_name': app.config.get('STOP_A_NAME', "Swan's Island"),
        'stop_b_name': app.config.get('STOP_B_NAME', 'Bass Harbor'),
        'stop_a_trips': stop_a_trips,
        'stop_b_trips': stop_b_trips,
        'date_display': day_date.strftime('%A, %B %-d, %Y'),
        'has_service': bool(trips),
    }
    if day_date.weekday() == 2:  # Wednesday
        context['note'] = _wednesday_note(day_date)
    return context

def _build_schedule_context():
    """Build the template context for the live "today" schedule.

    Classifies each of today's trips as past/active/future, flags the single
    soonest upcoming departure, assembles any in-progress voyages with a
    progress percentage, and includes the dev time-override fields. Respects
    the ?now= override via _current_datetime.
    """
    route_id = app.config.get('ROUTE_ID', '1000')
    stop_a_id = app.config.get('STOP_A_ID', '1001')
    stop_b_id = app.config.get('STOP_B_ID', '1002')

    now_dt = _current_datetime()
    now = now_dt.time()
    now_seconds = now.hour * 3600 + now.minute * 60 + now.second

    route = Route(feed, route_id)
    trips = [t.get_trip_summary() for t in route.get_trips_on_date(now_dt.strftime('%Y%m%d'))]

    stop_a_trips, stop_b_trips = [], []
    for trip in trips:
        dep = _parse_gtfs_time(trip['departure_time'])
        arr = _parse_gtfs_time(trip['arrival_time'])
        if arr < now:
            trip['status'] = 'past'
        elif dep <= now <= arr:
            trip['status'] = 'active'
        else:
            trip['status'] = 'future'
        trip['display_time'] = _format_display_time(trip['departure_time'])
        trip['countdown'] = _format_countdown(trip['departure_time'], now_seconds)

        if trip['originating_stop']['stop_id'] == stop_a_id:
            stop_a_trips.append(trip)
        elif trip['originating_stop']['stop_id'] == stop_b_id:
            stop_b_trips.append(trip)

    next_a = next((t for t in stop_a_trips if t['status'] == 'future'), None)
    next_b = next((t for t in stop_b_trips if t['status'] == 'future'), None)
    # Highlight only THE single next departure to leave (soonest across both ports),
    # not the next from each port. stop_*_trips hold the same dict objects as `trips`,
    # so flagging here is reflected in the rendered columns.
    upcoming = [t for t in trips if t['status'] == 'future']
    if upcoming:
        soonest = min(upcoming, key=lambda t: _gtfs_seconds(t['departure_time']))
        soonest['is_next'] = True

    if next_a:
        next_a['countdown'] = _format_countdown(next_a['departure_time'], now_seconds)
    if next_b:
        next_b['countdown'] = _format_countdown(next_b['departure_time'], now_seconds)

    active_trips = []
    for trip in trips:
        if trip['status'] != 'active':
            continue
        active_trips.append({
            'from_name': trip['originating_stop']['stop_name'],
            'to_name': trip['destination_stop']['stop_name'],
            'dep_display': trip['display_time'],
            'arr_display': _format_display_time(trip['arrival_time']),
            'progress_pct': _trip_progress_pct(
                trip['departure_time'], trip['arrival_time'], now_seconds),
        })

    dev_mode = bool(app.config.get('DEV_MODE'))
    override = request.args.get('now') if dev_mode else None
    now_qs = '?now=' + quote(override) if override else ''

    stop_a_name = app.config.get('STOP_A_NAME', "Swan's Island")
    stop_b_name = app.config.get('STOP_B_NAME', 'Bass Harbor')

    return {
        'stop_a_name': stop_a_name,
        'stop_b_name': stop_b_name,
        'stop_a_maps': _maps_links(stop_a_id, stop_a_name),
        'stop_b_maps': _maps_links(stop_b_id, stop_b_name),
        'stop_a_trips': stop_a_trips,
        'stop_b_trips': stop_b_trips,
        'next_a': next_a,
        'next_b': next_b,
        'active_trips': active_trips,
        'today': now_dt.strftime('%A, %B %-d, %Y'),
        'dev_mode': dev_mode,
        'now_qs': now_qs,
        'now_input': now_dt.strftime('%Y-%m-%dT%H:%M'),
        'wednesday_note': _wednesday_note(now_dt.date()) if now_dt.weekday() == 2 else None,
    }

@app.route("/")
def index():
    """Render the home page: today's live schedule and next/in-progress info."""
    return render_template('index.html', **_build_schedule_context())

@app.route("/schedule/fragment")
def schedule_fragment():
    """Render the HTMX fragment the home page polls every 60s."""
    return render_template('_schedule.html', **_build_schedule_context())

@app.route("/schedule")
def schedule():
    """Render the weekly (Mon-Sun) calendar for the current week."""
    route = Route(feed, app.config.get('ROUTE_ID', '1000'))
    stop_a_name = app.config.get('STOP_A_NAME', "Swan's Island")
    stop_b_name = app.config.get('STOP_B_NAME', 'Bass Harbor')
    week = route.get_week_schedule(_current_datetime().date())
    week_label = (f"{week[0]['date'].strftime('%b %-d')} – "
                  f"{week[-1]['date'].strftime('%-d, %Y')}")
    return render_template(
        'schedule.html',
        stop_a_name=stop_a_name,
        stop_b_name=stop_b_name,
        stop_a_abbr=_abbreviate(stop_a_name),
        stop_b_abbr=_abbreviate(stop_b_name),
        week=week,
        week_label=week_label,
    )

@app.route("/by-day")
def by_day():
    """Render the comprehensive schedule: every day-type pattern, stacked vertically."""
    route = Route(feed, app.config.get('ROUTE_ID', '1000'))
    stop_a_name = app.config.get('STOP_A_NAME', "Swan's Island")
    stop_b_name = app.config.get('STOP_B_NAME', 'Bass Harbor')
    return render_template(
        'byday.html',
        stop_a_name=stop_a_name,
        stop_b_name=stop_b_name,
        stop_a_abbr=_abbreviate(stop_a_name),
        stop_b_abbr=_abbreviate(stop_b_name),
        days=route.get_comprehensive_schedule(),
    )

@app.route("/date")
def date_lookup():
    """Render the date-picker page, prefilled with today's sailings."""
    today = _current_datetime().date()
    return render_template(
        'datepick.html',
        today=today.isoformat(),
        **_build_date_context(today.strftime('%Y%m%d')),
    )

@app.route("/date/fragment")
def date_fragment():
    """Render the date-lookup card for the chosen date (HTMX target)."""
    raw = request.args.get('date', '')
    try:
        day_date = date.fromisoformat(raw)
    except ValueError:
        day_date = _current_datetime().date()
    return render_template('_date_card.html', **_build_date_context(day_date.strftime('%Y%m%d')))

@app.route("/map")
def vessel_map():
    """Render the live AIS map (VesselFinder embed) framed on both terminals."""
    stop_a = Stop(feed, app.config.get('STOP_A_ID', '1001'))
    stop_b = Stop(feed, app.config.get('STOP_B_ID', '1002'))
    return render_template(
        'map.html',
        stop_a_name=app.config.get('STOP_A_NAME', "Swan's Island"),
        stop_b_name=app.config.get('STOP_B_NAME', 'Bass Harbor'),
        center_lat=(stop_a.stop_lat + stop_b.stop_lat) / 2,
        center_lon=(stop_a.stop_lon + stop_b.stop_lon) / 2,
        zoom=12,
    )

@app.route("/about")
def about():
    """Render the About page (prose + Buy Me a Coffee; linked from the footer only)."""
    return render_template('about.html')

@app.route("/prefs/time-format")
def toggle_time_format():
    """Flip the 12-/24-hour time preference, persist it in a cookie, and go back."""
    new = '12' if _use_military() else '24'
    resp = redirect(request.referrer or '/')
    resp.set_cookie('time_format', new, max_age=60 * 60 * 24 * 365, samesite='Lax')
    return resp

@app.route("/prefs/map-provider")
def set_map_provider():
    """Persist the preferred maps provider in a cookie and return to the prior page.

    Backs the footer Apple/Google toggle, which only appears once a provider has
    been chosen (here or via the next-departure modal, which sets the same cookie).
    """
    provider = request.args.get('provider')
    resp = redirect(request.referrer or '/')
    if provider in ('apple', 'google'):
        resp.set_cookie('map_provider', provider, max_age=60 * 60 * 24 * 365, samesite='Lax')
    return resp

if __name__ == '__main__':
    app.run(debug=app.config.get('DEV_MODE', False), port=8000)
