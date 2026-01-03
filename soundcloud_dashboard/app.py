"""
SoundCloud Insights Dashboard
A Flask-based dashboard for exploring your SoundCloud geographic data.

Usage:
    pip install flask
    python app.py

Then open http://localhost:5000
"""

from flask import Flask, render_template, jsonify, send_from_directory
import json
import os

app = Flask(__name__)

# Load data
DATA = None

def load_data():
    global DATA
    data_file = os.path.join(os.path.dirname(__file__), 'soundcloud_insights.json')
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            DATA = json.load(f)
        print(f"✓ Loaded data: {len(DATA.get('tracks', []))} tracks")
    else:
        print(f"⚠ No data file found at {data_file}")
        print("  Run soundcloud_insights.py first to generate data.")
        DATA = {"tracks": [], "aggregate": {"countries": [], "cities": []}, "country_tracks": {}}


# City coordinates for the map
CITY_COORDS = {
    "Chicago": [41.8781, -87.6298],
    "Montreal": [45.5017, -73.5673],
    "Hanoi": [21.0285, 105.8542],
    "Toronto": [43.6532, -79.3832],
    "Ho Chi Minh City": [10.8231, 106.6297],
    "Washington": [38.9072, -77.0369],
    "New York": [40.7128, -74.0060],
    "Miami": [25.7617, -80.1918],
    "Kyiv": [50.4501, 30.5234],
    "Cairo": [30.0444, 31.2357],
    "Da Nang": [16.0544, 108.2022],
    "Lviv": [49.8397, 24.0297],
    "Gangnam-gu": [37.5172, 127.0473],
    "Denpasar": [-8.6705, 115.2126],
    "Los Angeles": [34.0522, -118.2437],
    "Dnipro": [48.4647, 35.0462],
    "Jakarta": [-6.2088, 106.8456],
    "Medan": [3.5952, 98.6722],
    "Frankfurt am Main": [50.1109, 8.6821],
    "Melbourne": [-37.8136, 144.9631],
    "Minsk": [53.9006, 27.5590],
    "Gwanak-gu": [37.4784, 126.9516],
    "Sydney": [-33.8688, 151.2093],
    "Riyadh": [24.7136, 46.6753],
    "Warsaw": [52.2297, 21.0122],
    "Paris": [48.8566, 2.3522],
    "Upland": [34.0975, -117.6484],
    "Wroclaw": [51.1079, 17.0385],
    "Chisinau": [47.0105, 28.8638],
    "Jeddah": [21.4858, 39.1925],
    "Biên Hòa": [10.9574, 106.8426],
    "Pekanbaru": [0.5071, 101.4478],
    "Haiphong": [20.8449, 106.6881],
    "Orlando": [28.5383, -81.3792],
    "Kuwait City": [29.3759, 47.9774],
    "Rio de Janeiro": [-22.9068, -43.1729],
    "Amsterdam": [52.3676, 4.9041],
    "Seoul": [37.5665, 126.9780],
    "Brooklyn": [40.6782, -73.9442],
    "Ulan Bator": [47.8864, 106.9057],
    "Hải Dương": [20.9373, 106.3146],
    "Dammam": [26.4207, 50.0888],
    "Dongjak-gu": [37.5124, 126.9393],
    "Riverside": [33.9533, -117.3962],
    "The Bronx": [40.8448, -73.8648],
    "Surabaya": [-7.2575, 112.7521],
    "Lahore": [31.5204, 74.3587],
    "Singapore": [1.3521, 103.8198],
    "Buon Ma Thuot": [12.6667, 108.0500],
    "Vilnius": [54.6872, 25.2797],
    "London": [51.5074, -0.1278],
    "Berlin": [52.5200, 13.4050],
    "Tokyo": [35.6762, 139.6503],
    "Bangkok": [13.7563, 100.5018],
    "Mumbai": [19.0760, 72.8777],
    "São Paulo": [-23.5505, -46.6333],
    "Mexico City": [19.4326, -99.1332],
    "Dubai": [25.2048, 55.2708],
}


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/api/summary')
def api_summary():
    """Get summary stats."""
    if not DATA:
        return jsonify({"error": "No data loaded"})
    
    total_plays = sum(t.get('plays', 0) for t in DATA.get('tracks', []))
    
    return jsonify({
        "total_plays": total_plays,
        "total_tracks": len(DATA.get('tracks', [])),
        "total_countries": len(DATA.get('aggregate', {}).get('countries', [])),
        "total_cities": len(DATA.get('aggregate', {}).get('cities', [])),
        "top_track": DATA.get('tracks', [{}])[0].get('title', 'N/A') if DATA.get('tracks') else 'N/A',
        "top_track_plays": DATA.get('tracks', [{}])[0].get('plays', 0) if DATA.get('tracks') else 0,
        "username": DATA.get('user', {}).get('username', 'unknown'),
    })


@app.route('/api/tracks')
def api_tracks():
    """Get all tracks."""
    tracks = DATA.get('tracks', [])
    return jsonify(tracks)


@app.route('/api/track/<track_urn>')
def api_track(track_urn):
    """Get a specific track with its geo data."""
    # Handle URL-encoded colons
    track_urn = track_urn.replace('%3A', ':')
    
    for track in DATA.get('tracks', []):
        if track.get('urn') == track_urn or track.get('urn', '').endswith(track_urn):
            return jsonify(track)
    
    return jsonify({"error": "Track not found"}), 404


@app.route('/api/countries')
def api_countries():
    """Get aggregate country data."""
    countries = DATA.get('aggregate', {}).get('countries', [])
    return jsonify(countries)


@app.route('/api/country/<country_code>')
def api_country(country_code):
    """Get tracks for a specific country."""
    country_data = DATA.get('country_tracks', {}).get(country_code.upper())
    
    if country_data:
        return jsonify(country_data)
    
    return jsonify({"error": "Country not found"}), 404


@app.route('/api/country/<country_code>/cities')
def api_country_cities(country_code):
    """Get cities for a specific country."""
    all_cities = DATA.get('aggregate', {}).get('cities', [])
    country_cities = [c for c in all_cities if c.get('country_code', '').upper() == country_code.upper()]
    
    return jsonify(country_cities)


@app.route('/api/cities')
def api_cities():
    """Get aggregate city data with coordinates."""
    cities = DATA.get('aggregate', {}).get('cities', [])
    
    # Add coordinates
    cities_with_coords = []
    for city in cities:
        city_copy = city.copy()
        coords = CITY_COORDS.get(city['name'])
        if coords:
            city_copy['lat'] = coords[0]
            city_copy['lng'] = coords[1]
        cities_with_coords.append(city_copy)
    
    return jsonify(cities_with_coords)


@app.route('/api/map-data')
def api_map_data():
    """Get all data needed for the map."""
    cities = DATA.get('aggregate', {}).get('cities', [])
    countries = DATA.get('aggregate', {}).get('countries', [])
    
    # Add coordinates to cities
    cities_with_coords = []
    for city in cities:
        coords = CITY_COORDS.get(city['name'])
        if coords:
            cities_with_coords.append({
                "name": city['name'],
                "country": city.get('country', ''),
                "country_code": city.get('country_code', ''),
                "plays": city['plays'],
                "lat": coords[0],
                "lng": coords[1]
            })
    
    # Create country code -> plays mapping
    country_plays = {c['code']: c['plays'] for c in countries}
    
    return jsonify({
        "cities": cities_with_coords,
        "country_plays": country_plays
    })


if __name__ == '__main__':
    load_data()
    print("\n🚀 Starting SoundCloud Insights Dashboard")
    print("   Open http://localhost:5000 in your browser\n")
    app.run(debug=True, port=5000)
