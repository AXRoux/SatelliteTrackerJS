from flask import Flask, render_template, jsonify, request
import requests
import json
from config import Config
import logging
import time

app = Flask(__name__)
app.config.from_object(Config)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Add a simple cache
cache = {}
CACHE_DURATION = 300  # 5 minutes

@app.route('/')
def index():
    return render_template('index.html', config=app.config)

@app.route('/api/satellites/<int:category>')
def get_satellites(category):
    limit = request.args.get('limit', default=5, type=int)
    search_query = request.args.get('search', default='', type=str)
    url = f"https://api.n2yo.com/rest/v1/satellite/above/{app.config['OBSERVER_LAT']}/{app.config['OBSERVER_LON']}/{app.config['OBSERVER_ALT']}/90/{category}/&apiKey={app.config['N2YO_API_KEY']}"
    
    # Check cache first
    cache_key = f"category_{category}"
    if cache_key in cache and time.time() - cache[cache_key]['timestamp'] < CACHE_DURATION:
        app.logger.info(f"Returning cached data for category {category}")
        data = cache[cache_key]['data']
    else:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'above' not in data:
                app.logger.error(f"Unexpected API response structure: {data}")
                return jsonify({"error": "Unexpected API response structure"}), 500
            
            # Update cache
            cache[cache_key] = {
                'timestamp': time.time(),
                'data': data
            }
            
            app.logger.info(f"Fetched and cached satellite data for category {category}")
        except requests.RequestException as e:
            app.logger.error(f"Error fetching satellite data: {str(e)}")
            
            # Check if we have cached data to return as fallback
            if cache_key in cache:
                app.logger.info(f"Returning stale cached data for category {category}")
                data = cache[cache_key]['data']
            else:
                return jsonify({"error": "Failed to fetch satellite data"}), 500

    # Filter satellites based on search query
    if search_query:
        data['above'] = [sat for sat in data['above'] if search_query.lower() in sat['satname'].lower()]

    data['above'] = data['above'][:limit]
    return jsonify(data)

@app.route('/api/satellite/<int:satid>')
def get_satellite_position(satid):
    url = f"https://api.n2yo.com/rest/v1/satellite/positions/{satid}/{app.config['OBSERVER_LAT']}/{app.config['OBSERVER_LON']}/{app.config['OBSERVER_ALT']}/1/&apiKey={app.config['N2YO_API_KEY']}"
    app.logger.debug(f"Fetching satellite position from URL: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        app.logger.info(f"Fetched satellite position: {json.dumps(data)}")
        return jsonify(data)
    except requests.RequestException as e:
        app.logger.error(f"Error fetching satellite position: {str(e)}")
        return jsonify({"error": "Failed to fetch satellite position"}), 500

@app.route('/api/satellite/<int:satid>/trajectory')
def get_satellite_trajectory(satid):
    seconds = request.args.get('seconds', default=300, type=int)
    url = f"https://api.n2yo.com/rest/v1/satellite/positions/{satid}/{app.config['OBSERVER_LAT']}/{app.config['OBSERVER_LON']}/{app.config['OBSERVER_ALT']}/{seconds}/&apiKey={app.config['N2YO_API_KEY']}"
    app.logger.debug(f"Fetching satellite trajectory from URL: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        app.logger.info(f"Fetched satellite trajectory: {json.dumps(data)}")
        return jsonify(data)
    except requests.RequestException as e:
        app.logger.error(f"Error fetching satellite trajectory: {str(e)}")
        return jsonify({"error": "Failed to fetch satellite trajectory"}), 500

@app.route('/api/satellite/<int:satid>/info')
def get_satellite_info(satid):
    url = f"https://api.n2yo.com/rest/v1/satellite/tle/{satid}&apiKey={app.config['N2YO_API_KEY']}"
    app.logger.debug(f"Fetching detailed satellite info from URL: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        app.logger.info(f"Fetched detailed satellite info: {json.dumps(data)}")
        return jsonify(data)
    except requests.RequestException as e:
        app.logger.error(f"Error fetching detailed satellite info: {str(e)}")
        return jsonify({"error": "Failed to fetch detailed satellite info"}), 500

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
