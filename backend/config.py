"""Flask configuration, loaded via app.config.from_pyfile.

Defines the environment flag (DEV_MODE), the GTFS feed path, and the route/stop
identifiers and display names for the single supported ferry route.
"""
import os
from datetime import date

# Single source of truth for the environment. Set MSFSGTFS_ENV=production to disable
# development-only tooling (e.g. the ?now= time override + debug bar).
ENV = os.getenv('MSFSGTFS_ENV', 'development')
DEV_MODE = ENV == 'development'

# NOTE: DEBUG is a Flask-owned key — the `flask run` CLI overrides it from FLASK_DEBUG,
# so it is NOT reliable for gating app features. Gate dev tooling on DEV_MODE instead.
DEBUG = DEV_MODE
SECRET_KEY = os.urandom(24)

GTFS_FEED_PATH = "Archive.zip"
ROUTE_ID = "1000"
STOP_A_ID = "1001"
STOP_A_NAME = "Swan's Island"
STOP_B_ID = "1002"
STOP_B_NAME = "Bass Harbor"

# Site-wide toast notice, shown through NOTICE_LAST_DAY unless dismissed. The
# dismissal cookie stores NOTICE_ID, so a future notice needs only a new id.
NOTICE_ID = "winter-2026"
NOTICE_MESSAGE = "Heads up! The schedule has been updated for the Winter Ferry Schedule."
NOTICE_LAST_DAY = date(2026, 11, 14)
