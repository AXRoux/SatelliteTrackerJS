from flask import Flask, render_template, jsonify, request
import requests
import json
from config import Config
import logging
import os
import time

app = Flask(__name__)
app.config.from_object(Config)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Print masked API key for verification
api_key = os.environ.get('N2YO_API_KEY')
if api_key:
    masked_key = '*' * (len(api_key) - 4) + api_key[-4:]
    app.logger.info(f"N2YO API Key is set. Masked key: {masked_key}")
else:
    app.logger.error("N2YO API Key is not set in environment variables")

# Simple rate limiter
last_request_time = 0
min_request_interval = 10  # Increased to 10 seconds

@app.route('/')
def index():
    return render_template('index.html', config=app.config)

def handle_rate_limit(e):
    app.logger.warning("Rate limit exceeded. Please wait before making another request.")
    return jsonify({"error": "Rate limit exceeded. Please wait before making another request."}), 429

def make_n2yo_request(url):
    global last_request_time
    current_time = time.time()
    
    if current_time - last_request_time < min_request_interval:
        return handle_rate_limit(None)

    last_request_time = current_time

    try:
        response = requests.get(url)
        if response.status_code == 429:
            app.logger.error("N2YO API rate limit exceeded")
            return handle_rate_limit(None)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        app.logger.error(f"Error making N2YO API request: {str(e)}")
        return jsonify({"error": "Failed to fetch data from N2YO API"}), 500

@app.route('/api/satellites/<int:category>')
def get_satellites(category):
    limit = request.args.get('limit', default=5, type=int)
    url = f"https://api.n2yo.com/rest/v1/satellite/above/{app.config['OBSERVER_LAT']}/{app.config['OBSERVER_LON']}/{app.config['OBSERVER_ALT']}/90/{category}/&apiKey={app.config['N2YO_API_KEY']}"
    app.logger.debug(f"Fetching satellites from URL: {url}")
    
    data = make_n2yo_request(url)
    if isinstance(data, tuple):  # Error response
        return data
    
    if 'above' in data:
        data['above'] = data['above'][:limit]
        app.logger.info(f"Fetched satellite data: {json.dumps(data)}")
        return jsonify(data)
    else:
        app.logger.error(f"Unexpected response format: {json.dumps(data)}")
        return jsonify({"error": "Unexpected response format from N2YO API"}), 500

@app.route('/api/satellite/<int:satid>')
def get_satellite_position(satid):
    url = f"https://api.n2yo.com/rest/v1/satellite/positions/{satid}/{app.config['OBSERVER_LAT']}/{app.config['OBSERVER_LON']}/{app.config['OBSERVER_ALT']}/1/&apiKey={app.config['N2YO_API_KEY']}"
    app.logger.debug(f"Fetching satellite position from URL: {url}")
    
    data = make_n2yo_request(url)
    if isinstance(data, tuple):  # Error response
        return data
    
    app.logger.info(f"Fetched satellite position: {json.dumps(data)}")
    return jsonify(data)

@app.route('/api/satellite/<int:satid>/trajectory')
def get_satellite_trajectory(satid):
    seconds = request.args.get('seconds', default=300, type=int)
    url = f"https://api.n2yo.com/rest/v1/satellite/positions/{satid}/{app.config['OBSERVER_LAT']}/{app.config['OBSERVER_LON']}/{app.config['OBSERVER_ALT']}/{seconds}/&apiKey={app.config['N2YO_API_KEY']}"
    app.logger.debug(f"Fetching satellite trajectory from URL: {url}")
    
    data = make_n2yo_request(url)
    if isinstance(data, tuple):  # Error response
        return data
    
    app.logger.info(f"Fetched satellite trajectory: {json.dumps(data)}")
    return jsonify(data)

@app.route('/api/satellite/<int:satid>/info')
def get_satellite_info(satid):
    url = f"https://api.n2yo.com/rest/v1/satellite/tle/{satid}&apiKey={app.config['N2YO_API_KEY']}"
    app.logger.debug(f"Fetching detailed satellite info from URL: {url}")
    
    data = make_n2yo_request(url)
    if isinstance(data, tuple):  # Error response
        return data
    
    app.logger.info(f"Fetched detailed satellite info: {json.dumps(data)}")
    return jsonify(data)

@app.route('/api/categories')
def get_categories():
    categories = [
        {"id": 0, "name": "All"},
        {"id": 1, "name": "Brightest"},
        {"id": 2, "name": "ISS"},
        {"id": 3, "name": "Weather"},
        {"id": 4, "name": "NOAA"},
        {"id": 18, "name": "Amateur radio"},
        {"id": 22, "name": "Galileo"},
        {"id": 23, "name": "Satellite-Based Augmentation System"},
        {"id": 24, "name": "Navy Navigation Satellite System"},
        {"id": 25, "name": "Russian LEO Navigation"}
    ]
    app.logger.info(f"Returning categories: {json.dumps(categories)}")
    return jsonify(categories)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
