"""
SoundCloud Insights Scraper (GraphQL Version)
Pulls geographic data (countries, cities) per track from SoundCloud Insights.

Setup:
  Set your OAuth token as an environment variable:
    Windows:  set SOUNDCLOUD_OAUTH_TOKEN=your_token_here
    Mac/Linux: export SOUNDCLOUD_OAUTH_TOKEN=your_token_here
  
  Or create a .env file with:
    SOUNDCLOUD_OAUTH_TOKEN=your_token_here

Usage: python soundcloud_insights.py

Output: 
  - soundcloud_insights.json (complete data with per-track breakdown)
  - soundcloud_countries.csv
  - soundcloud_cities.csv
  - soundcloud_top_tracks.csv
"""

import csv
import json
import os
import requests
import time

# Load from .env file if it exists
def load_env():
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

load_env()

# Configuration
OAUTH_TOKEN = os.environ.get("SOUNDCLOUD_OAUTH_TOKEN")
GRAPHQL_URL = "https://graph.soundcloud.com/graphql"

if not OAUTH_TOKEN:
    print("❌ Error: SOUNDCLOUD_OAUTH_TOKEN environment variable not set.")
    print("")
    print("   To get your token:")
    print("   1. Log into SoundCloud in Chrome")
    print("   2. Go to your Insights page")
    print("   3. Open DevTools (F12) → Application → Cookies")
    print("   4. Find 'oauth_token' and copy its value")
    print("")
    print("   Then set it:")
    print("   Windows:   set SOUNDCLOUD_OAUTH_TOKEN=your_token_here")
    print("   Mac/Linux: export SOUNDCLOUD_OAUTH_TOKEN=your_token_here")
    print("   Or create a .env file with: SOUNDCLOUD_OAUTH_TOKEN=your_token_here")
    exit(1)

HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "apollographql-client-name": "insights-ui",
    "apollographql-client-version": "0.1.0",
    "authorization": f"OAuth {OAUTH_TOKEN}",
    "content-type": "application/json",
    "origin": "https://insights-ui.soundcloud.com",
    "referer": "https://insights-ui.soundcloud.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
}

# GraphQL Queries
QUERY_TOP_CITIES = """
query TopCitiesByWindow($metric: MetricType!, $windowInput: TimeWindowInput!, $trackUrn: String) {
  topCitiesByWindow(metric: $metric, windowInput: $windowInput, trackUrn: $trackUrn) {
    count
    city {
      name
      country {
        name
        countryCode
      }
    }
  }
}
"""

QUERY_TOP_COUNTRIES = """
query TopCountriesByWindow($metric: MetricType!, $windowInput: TimeWindowInput!, $trackUrn: String) {
  topCountriesByWindow(metric: $metric, windowInput: $windowInput, trackUrn: $trackUrn) {
    count
    country {
      name
      countryCode
    }
  }
}
"""

QUERY_TOP_TRACKS = """
query TopTracksByWindow($metric: MetricType!, $windowInput: TimeWindowInput!) {
  topTracksByWindow(metric: $metric, windowInput: $windowInput) {
    count
    track {
      urn
      title
      artworkUrl
      permalink
      permalinkUrl
      createdAt
    }
  }
}
"""

QUERY_ME = """
query Me {
  me {
    avatarUrl
    city
    country
    createdAt
    features
    followersCount
    isPro
    permalink
    permalinkUrl
    urn
    username
  }
}
"""


def graphql_request(query, variables=None, operation_name=None):
    """Make a GraphQL request to SoundCloud."""
    payload = {
        "query": query,
        "variables": variables or {},
    }
    if operation_name:
        payload["operationName"] = operation_name
    
    response = requests.post(GRAPHQL_URL, headers=HEADERS, json=payload)
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(f"   Response: {response.text[:500]}")
        return None
    
    data = response.json()
    if "errors" in data:
        print(f"❌ GraphQL Error: {data['errors']}")
        return None
    
    return data.get("data")


def get_me():
    """Get current user info."""
    return graphql_request(QUERY_ME, operation_name="Me")


def get_top_cities(timewindow="DAYS_30", limit=50, track_urn=None):
    """Get top cities by plays."""
    variables = {
        "metric": "PLAYS",
        "windowInput": {"timewindow": timewindow, "limit": limit},
        "trackUrn": track_urn
    }
    return graphql_request(QUERY_TOP_CITIES, variables, "TopCitiesByWindow")


def get_top_countries(timewindow="DAYS_30", limit=50, track_urn=None):
    """Get top countries by plays."""
    variables = {
        "metric": "PLAYS",
        "windowInput": {"timewindow": timewindow, "limit": limit},
        "trackUrn": track_urn
    }
    return graphql_request(QUERY_TOP_COUNTRIES, variables, "TopCountriesByWindow")


def get_top_tracks(timewindow="DAYS_30", limit=50):
    """Get top tracks by plays."""
    variables = {
        "metric": "PLAYS",
        "windowInput": {"timewindow": timewindow, "limit": limit}
    }
    return graphql_request(QUERY_TOP_TRACKS, variables, "TopTracksByWindow")


def main():
    print("\n🚀 SoundCloud Insights Scraper (Per-Track Edition)")
    print("=" * 55)
    
    # Verify auth
    print("🔐 Checking authentication...")
    me_data = get_me()
    
    if not me_data or not me_data.get("me"):
        print("❌ Authentication failed. Your oauth_token may have expired.")
        return
    
    me = me_data["me"]
    print(f"👤 Logged in as: {me.get('username', 'unknown')}")
    print(f"   Followers: {me.get('followersCount', 0):,}")
    print(f"   Pro: {me.get('isPro', False)}")
    
    # Get top tracks first
    print("\n🎵 Fetching top tracks (last 30 days)...")
    tracks_data = get_top_tracks(limit=50)
    
    if not tracks_data or not tracks_data.get("topTracksByWindow"):
        print("❌ No tracks found.")
        return
    
    tracks = tracks_data["topTracksByWindow"]
    print(f"   Found {len(tracks)} tracks")
    
    # Get aggregate geo data
    print("\n🌍 Fetching aggregate geographic data...")
    
    agg_countries_data = get_top_countries()
    agg_countries = agg_countries_data.get("topCountriesByWindow", []) if agg_countries_data else []
    print(f"   Countries: {len(agg_countries)}")
    
    agg_cities_data = get_top_cities()
    agg_cities = agg_cities_data.get("topCitiesByWindow", []) if agg_cities_data else []
    print(f"   Cities: {len(agg_cities)}")
    
    # Now get per-track geo data for top tracks
    print(f"\n📊 Fetching per-track geographic data...")
    print("-" * 55)
    
    tracks_with_geo = []
    
    # Limit to top 20 tracks to avoid rate limiting
    for i, track_item in enumerate(tracks[:20], 1):
        track = track_item["track"]
        track_urn = track["urn"]
        title = track["title"][:35]
        
        print(f"   [{i}/20] {title}...", end=" ", flush=True)
        
        # Get countries for this track
        countries_data = get_top_countries(track_urn=track_urn)
        track_countries = []
        if countries_data and countries_data.get("topCountriesByWindow"):
            track_countries = countries_data["topCountriesByWindow"]
        
        # Small delay to be nice to the API
        time.sleep(0.3)
        
        # Get cities for this track
        cities_data = get_top_cities(track_urn=track_urn)
        track_cities = []
        if cities_data and cities_data.get("topCitiesByWindow"):
            track_cities = cities_data["topCitiesByWindow"]
        
        print(f"✓ {len(track_countries)} countries, {len(track_cities)} cities")
        
        tracks_with_geo.append({
            "urn": track_urn,
            "title": track["title"],
            "plays": track_item["count"],
            "url": track["permalinkUrl"],
            "artwork": track["artworkUrl"],
            "created_at": track["createdAt"][:10] if track["createdAt"] else "",
            "countries": [
                {
                    "name": c["country"]["name"],
                    "code": c["country"]["countryCode"],
                    "plays": c["count"]
                }
                for c in track_countries
            ],
            "cities": [
                {
                    "name": c["city"]["name"],
                    "country": c["city"]["country"]["name"],
                    "country_code": c["city"]["country"]["countryCode"],
                    "plays": c["count"]
                }
                for c in track_cities
            ]
        })
        
        # Rate limit protection
        time.sleep(0.3)
    
    # Build country -> tracks mapping
    print("\n🔄 Building country-to-tracks mapping...")
    country_tracks = {}
    for track in tracks_with_geo:
        for country in track["countries"]:
            code = country["code"]
            if code not in country_tracks:
                country_tracks[code] = {
                    "name": country["name"],
                    "code": code,
                    "total_plays": 0,
                    "tracks": []
                }
            country_tracks[code]["total_plays"] += country["plays"]
            country_tracks[code]["tracks"].append({
                "title": track["title"],
                "urn": track["urn"],
                "plays": country["plays"]
            })
    
    # Sort tracks within each country by plays
    for code in country_tracks:
        country_tracks[code]["tracks"].sort(key=lambda x: x["plays"], reverse=True)
    
    # Save everything to JSON
    print("\n💾 Saving data...")
    
    all_data = {
        "user": me,
        "aggregate": {
            "countries": [
                {
                    "rank": i + 1,
                    "name": c["country"]["name"],
                    "code": c["country"]["countryCode"],
                    "plays": c["count"]
                }
                for i, c in enumerate(agg_countries)
            ],
            "cities": [
                {
                    "rank": i + 1,
                    "name": c["city"]["name"],
                    "country": c["city"]["country"]["name"],
                    "country_code": c["city"]["country"]["countryCode"],
                    "plays": c["count"]
                }
                for i, c in enumerate(agg_cities)
            ],
        },
        "tracks": tracks_with_geo,
        "country_tracks": country_tracks,
    }
    
    with open("soundcloud_insights.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    print("   ✓ soundcloud_insights.json")
    
    # Also save CSVs for convenience
    with open("soundcloud_countries.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "country", "country_code", "plays"])
        for i, c in enumerate(agg_countries, 1):
            writer.writerow([i, c["country"]["name"], c["country"]["countryCode"], c["count"]])
    print("   ✓ soundcloud_countries.csv")
    
    with open("soundcloud_cities.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "city", "country", "country_code", "plays"])
        for i, c in enumerate(agg_cities, 1):
            writer.writerow([i, c["city"]["name"], c["city"]["country"]["name"], c["city"]["country"]["countryCode"], c["count"]])
    print("   ✓ soundcloud_cities.csv")
    
    with open("soundcloud_top_tracks.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "title", "plays", "url", "created_at"])
        for i, t in enumerate(tracks, 1):
            writer.writerow([i, t["track"]["title"], t["count"], t["track"]["permalinkUrl"], t["track"]["createdAt"][:10] if t["track"]["createdAt"] else ""])
    print("   ✓ soundcloud_top_tracks.csv")
    
    # Summary
    print("\n" + "=" * 55)
    print("✅ COMPLETE!")
    print(f"   Tracks with geo data: {len(tracks_with_geo)}")
    print(f"   Countries: {len(agg_countries)}")
    print(f"   Cities: {len(agg_cities)}")
    print(f"   Country→Track mappings: {len(country_tracks)}")
    print("=" * 55)
    
    print("\n🏆 Top 5 Tracks:")
    for i, t in enumerate(tracks_with_geo[:5], 1):
        top_country = t["countries"][0]["name"] if t["countries"] else "N/A"
        print(f"   {i}. {t['title'][:30]}... — {t['plays']:,} plays (top: {top_country})")


if __name__ == "__main__":
    main()
