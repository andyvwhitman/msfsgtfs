from pathlib import Path

from datetime import datetime

import gtfs_kit as gk

from flask import Flask, render_template

app = Flask(__name__)
app.config.from_pyfile('config.py')

feed_path = Path(__file__).parent / app.config.get('GTFS_FEED_PATH', 'Archive.zip')
feed = gk.read_feed(feed_path, dist_units='mi')

WEEKDAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

class Route():
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
        date = datetime.now().strftime("%Y%m%d")
        return self.get_trips_on_date(date)

    def get_trips_on_date(self, date):
        all_trips = self.feed.get_trips(date=date)
        route_trips = all_trips[all_trips["route_id"] == self.route_id]

        return [Trip(self.feed, t.trip_id) for t in route_trips.itertuples()]

    def get_weekly_schedule(self):
        # Build the recurring weekly pattern straight from calendar.txt weekday flags
        # rather than date-based lookups: the feed's service window may not cover the
        # current date, so get_trips(date=...) can return empty even though the
        # recurring schedule is well-defined.
        calendar = self.feed.calendar
        schedule = {}
        for day in WEEKDAYS:
            service_ids = calendar[calendar[day].astype(int) == 1]['service_id'].astype(str)
            day_trips = self.feed.trips[
                (self.feed.trips['route_id'] == self.route_id)
                & (self.feed.trips['service_id'].astype(str).isin(service_ids))
            ]
            trips = [Trip(self.feed, t.trip_id).get_trip_summary() for t in day_trips.itertuples()]
            trips.sort(key=lambda t: t['departure_time'])
            for trip in trips:
                trip['display_time'] = _format_display_time(trip['departure_time'])
            schedule[day.capitalize()] = trips

        return schedule

class Trip():
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
        return Stop(self.feed, self.stop_times[0].stop_id)

    @property
    def destination_stop(self):
        return Stop(self.feed, self.stop_times[-1].stop_id)

    @property
    def departure_time(self):
        return self.stop_times[0].departure_time

    @property
    def arrival_time(self):
        return self.stop_times[-1].arrival_time

    def get_trip_summary(self):
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
        stop_summary = {}

        stop_summary['stop_id'] = self.stop_id
        stop_summary['stop_name'] = self.stop_name
        stop_summary['stop_desc'] = self.stop_desc
        stop_summary['stop_lat'] = self.stop_lat
        stop_summary['stop_lon'] = self.stop_lon

        return stop_summary

class StopTime():
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
    h, m, s = map(int, t.split(':'))
    if h >= 24:
        h -= 24
    return datetime.now().replace(hour=h, minute=m, second=s, microsecond=0).time()

def _format_display_time(t):
    h, m, _ = map(int, t.split(':'))
    if h >= 24:
        h -= 24
    period = 'AM' if h < 12 else 'PM'
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {period}"

def _build_schedule_context():
    route_id = app.config.get('ROUTE_ID', '1000')
    stop_a_id = app.config.get('STOP_A_ID', '1001')
    stop_b_id = app.config.get('STOP_B_ID', '1002')

    route = Route(feed, route_id)
    trips = [t.get_trip_summary() for t in route.get_trips_today()]
    now = datetime.now().time()

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

        if trip['originating_stop']['stop_id'] == stop_a_id:
            stop_a_trips.append(trip)
        elif trip['originating_stop']['stop_id'] == stop_b_id:
            stop_b_trips.append(trip)

    next_a = next((t for t in stop_a_trips if t['status'] == 'future'), None)
    next_b = next((t for t in stop_b_trips if t['status'] == 'future'), None)

    return {
        'stop_a_name': app.config.get('STOP_A_NAME', "Swan's Island"),
        'stop_b_name': app.config.get('STOP_B_NAME', 'Bass Harbor'),
        'stop_a_trips': stop_a_trips,
        'stop_b_trips': stop_b_trips,
        'next_a': next_a,
        'next_b': next_b,
        'today': datetime.now().strftime('%A, %B %-d, %Y'),
    }

@app.route("/")
def index():
    return render_template('index.html', **_build_schedule_context())

@app.route("/schedule/fragment")
def schedule_fragment():
    return render_template('_schedule.html', **_build_schedule_context())

@app.route("/schedule")
def schedule():
    route = Route(feed, app.config.get('ROUTE_ID', '1000'))
    return render_template(
        'schedule.html',
        stop_a_name=app.config.get('STOP_A_NAME', "Swan's Island"),
        stop_b_name=app.config.get('STOP_B_NAME', 'Bass Harbor'),
        weekly_schedule=route.get_weekly_schedule(),
    )

if __name__ == '__main__':
    app.run(debug=True, port=8000)
