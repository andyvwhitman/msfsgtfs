class Feed():
    def __init__(self, feed_publisher_name, feed_publisher_url, feed_lang, default_lang=None, feed_start_date=None, feed_end_date=None, feed_version=None, feed_contact_email=None, feed_contact_url=None):
        self.feed_publisher_name = feed_publisher_name
        self.feed_publisher_url = feed_publisher_url
        self.feed_lang = feed_lang
        self.default_lang = default_lang
        self.feed_start_date = feed_start_date
        self.feed_end_date = feed_end_date
        self.feed_version = feed_version
        self.feed_contact_email = feed_contact_email
        self.feed_contact_url = feed_contact_url

class Agency():
    def __init__(self, agency_id, agency_name, agency_url, agency_timezone, agency_lang=None, agency_phone=None, agency_fare_url=None, agency_email=None):
        self.agency_id = agency_id
        self.agency_name = agency_name
        self.agency_url = agency_url
        self.agency_timezone = agency_timezone
        self.agency_lang = agency_lang
        self.agency_phone = agency_phone
        self.agency_fare_url = agency_fare_url
        self.agency_email = agency_email

class Stop():
    def __init__(self, stop_id, stop_code=None, stop_name=None, tts_stop_name=None, stop_desc=None, stop_lat=None, stop_lon=None, zone_id=None, stop_url=None, location_type=None, parent_station=None, stop_timezone=None, wheelchair_boarding=None, level_id=None, platform_code=None):
        self.stop_id = stop_id
        self.stop_code = stop_code
        self.stop_name = stop_name
        self.tts_stop_name = tts_stop_name
        self.stop_desc = stop_desc
        self.stop_lat = stop_lat
        self.stop_lon = stop_lon
        self.zone_id = zone_id
        self.stop_url = stop_url
        self.location_type = location_type
        self.parent_station = parent_station
        self.stop_timezone = stop_timezone
        self.wheelchair_boarding = wheelchair_boarding
        self.level_id = level_id
        self.platform_code = platform_code

class Route():
    def __init__(self, route_id, route_type, agency_id=None, route_short_name=None, route_long_name=None, route_desc=None, route_url=None, route_color=None, route_text_color=None, route_sort_order=None, continuous_pickup=None, continuous_drop_off=None, network_id=None):
        self.route_id = route_id
        self.route_type = route_type
        self.agency_id = agency_id
        self.route_short_name = route_short_name
        self.route_long_name = route_long_name
        self.route_desc = route_desc
        self.route_url = route_url
        self.route_color = route_color
        self.route_text_color = route_text_color
        self.route_sort_order = route_sort_order
        self.continuous_pickup = continuous_pickup
        self.continuous_drop_off = continuous_drop_off
        self.network_id = network_id

class Trip():
    def __init__(self, route_id, service_id, trip_id, trip_headsign=None, trip_short_name=None, direction_id=None, block_id=None, shape_id=None, wheelchair_accessible=None, bikes_allowed=None):
        self.route_id = route_id
        self.service_id = service_id
        self.trip_id = trip_id
        self.trip_headsign = trip_headsign
        self.trip_short_name = trip_short_name
        self.direction_id = direction_id
        self.block_id = block_id
        self.shape_id = shape_id
        self.wheelchair_accessible = wheelchair_accessible
        self.bikes_allowed = bikes_allowed

class StopTime():
    def __init__(self, trip_id, stop_sequence, arrival_time=None, departure_time=None, stop_id=None, location_group_id=None, location_id=None, stop_headsign=None, start_pickup_drop_off_window=None, end_pickup_drop_off_window=None, pickup_type=None, drop_off_type=None, continuous_pickup=None, continuous_drop_off=None, shape_dist_traveled=None, timepoint=None, pickup_booking_rule_id=None, drop_off_booking_rule_id=None):
        self.trip_id = trip_id
        self.stop_sequence = stop_sequence
        self.arrival_time = arrival_time
        self.departure_time = departure_time
        self.stop_id = stop_id
        self.location_group_id = location_group_id
        self.location_id = location_id
        self.stop_headsign = stop_headsign
        self.start_pickup_drop_off_window = start_pickup_drop_off_window
        self.end_pickup_drop_off_window = end_pickup_drop_off_window
        self.pickup_type = pickup_type
        self.drop_off_type = drop_off_type
        self.continuous_pickup = continuous_pickup
        self.continuous_drop_off = continuous_drop_off
        self.shape_dist_traveled = shape_dist_traveled
        self.timepoint = timepoint
        self.pickup_booking_rule_id = pickup_booking_rule_id
        self.drop_off_booking_rule_id = drop_off_booking_rule_id

class Service():
    def __init__(self, service_id, monday, tuesday, wednesday, thursday, friday, saturday, sunday, start_date, end_date):
        self.service_id = service_id
        self.monday = monday
        self.tuesday = tuesday
        self.wednesday = wednesday
        self.thursday = thursday
        self.friday = friday
        self.saturday = saturday
        self.sunday = sunday
        self.start_date = start_date
        self.end_date = end_date

class ServiceException():
    def __init__(self, service_id, date, exception_type):
        self.service_id = service_id
        self.date = date
        self.exception_type = exception_type
