import os

class Config:
    N2YO_API_KEY = os.environ.get('N2YO_API_KEY')
    OBSERVER_LAT = 40.7128  # New York City latitude
    OBSERVER_LON = -74.0060  # New York City longitude
    OBSERVER_ALT = 0  # Sea level
    UPDATE_INTERVAL = 5000  # Update interval in milliseconds
