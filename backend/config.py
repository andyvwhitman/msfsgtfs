import os

DEBUG = os.getenv('MSFSGTFS_ENV', 'development') == 'development'
SECRET_KEY = os.urandom(24)

GTFS_FEED_PATH = "Archive.zip"
ROUTE_ID = "1000"
STOP_A_ID = "1001"
STOP_A_NAME = "Swan's Island"
STOP_B_ID = "1002"
STOP_B_NAME = "Bass Harbor"
