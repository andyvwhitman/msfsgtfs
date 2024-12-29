import sys
from pathlib import Path
import json

from datetime import datetime

import pandas as pd
import numpy as np
import geopandas as gp

import gtfs_kit as gk

from flask import Flask, abort

app = Flask(__name__)

feed_path = "Archive.zip"
feed = gk.read_feed(feed_path, dist_units='mi')

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

    def get_active_trip(self):
        current_datetime = datetime.now()
        current_date = current_datetime.strftime("%Y%m%d")
        current_time = current_datetime.strftime("%H:%M:%S")

        all_active_trips = feed.get_trips(date=current_date, time=current_time)
        
        try:
            route_active_trip = all_active_trips[all_active_trips["route_id"]== self.route_id].iloc[0]
            return Trip(self.feed, route_active_trip.trip_id)
        
        except:
            route_active_trip = None
            return None

    def get_next_trip(self):
        date = datetime.now().strftime("%Y%m%d")
        time = datetime.now().strftime("%H:%M:%D")

        route_timetable = self.feed.build_route_timetable(self.route_id, [date])
        route_departures = route_timetable[route_timetable["stop_sequence"] == 1]
        route_departures.loc[:, 'departure_time'] = pd.to_datetime(route_departures['departure_time'], format='%H:%M:%S').dt.time

        upcoming_departures = route_departures[route_departures["departure_time"] > datetime.now().time()]

        next_departure = upcoming_departures.iloc[0]

        return Trip(self.feed, next_departure.trip_id)

    def get_trips_today(self):
        date = datetime.now().strftime("%Y%m%d")
        return self.get_trips_on_date(date)

    def get_trips_on_date(self, date):
        all_trips = self.feed.get_trips(date=date)
        route_trips = all_trips[all_trips["route_id"] == self.route_id]

        return [Trip(self.feed, t.trip_id) for t in route_trips.itertuples()]

    def get_route_status(self):
        daily_summary = {}
        
        daily_trips = self.get_trips_today()

        if(len(daily_trips) > 0):
            daily_summary['all_trips'] = [t.get_trip_summary() for t in self.get_trips_today()]
        else:
            daily_trips['all_trips'] = []

        if(self.get_active_trip() != None):
            daily_summary['active_trip'] = self.get_active_trip().get_trip_summary()
        else:
            daily_summary['active_trip'] = None

        if(self.get_next_trip() != None):
            daily_summary['next_trip'] = self.get_next_trip().get_trip_summary()
        else:
            daily_summary['next_trip'] = None

        return daily_summary
        
    def get_route_status_json(self):
        return json.dumps(self.get_route_status())
    
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
    
    def get_trip_summary_json(self):
        return json.dumps(self.get_trip_summary())
    
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
    
    def get_stop_summary_json(self):
        return json.dumps(self.get_stop_summary())
    
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
    

@app.route("/")
def index():
    return "<h1>Hello There</h1>"

@app.route("/routes")
def all_routes():
    return json.dumps({"routes": feed.routes['route_id'].to_list()})

@app.route("/routes/<route_id>")
def route_summary(route_id):
    try:
        route = Route(feed, str(route_id))
        return route.get_route_status_json()
    except Exception as e:
        print(e)
        return abort(404)

@app.route("/trips/<trip_id>")
def trip_summary(trip_id):
    try:
        trip = Trip(feed, str(trip_id))
        return trip.get_trip_summary_json()
    except:
        return abort(404)

# main driver function
if __name__ == '__main__':

    # run() method of Flask class runs the application 
    # on the local development server.
    app.run()