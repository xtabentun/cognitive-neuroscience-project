"""
This file specifies how the flask app is configured.
"""

import os
from werkzeug.contrib.cache import SimpleCache


class Config(object):
    """
    The configuration parameters for the flask app.
    """
    SESSION_TYPE = 'memcached'

    # If there is an environment variable set with a secret key, use it:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'very_secret_key'

    # The database used can be the production database, the development
    # database (both online) or local if the user has MongoDB running locally.
    # Values DB can take are hence 'prod', 'dev', or 'local'. Defaults
    # to 'prod'.
    DB = os.environ.get('DB') or 'prod'
    CACHE = SimpleCache(default_timeout=1000000000000000000000)
