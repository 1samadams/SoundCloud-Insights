"""
SoundCloud Metrics Scraper (API Version)
Uses SoundCloud's internal API directly - no browser needed.

Setup:
  Set your OAuth token as an environment variable:
    Windows:   set SOUNDCLOUD_OAUTH_TOKEN=your_token_here
    Mac/Linux: export SOUNDCLOUD_OAUTH_TOKEN=your_token_here
  
  Or create a .env file with:
    SOUNDCLOUD_OAUTH_TOKEN=your_token_here

Usage: python soundcloud_scraper.py

Output: soundcloud_metrics.csv, soundcloud_metrics.json
"""

import csv
import json
import os
import requests

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
OUTPUT_FILE = "soundcloud_metrics.csv"
OAUTH_TOKEN = os.environ.get("SOUNDCLOUD_OAUTH_TOKEN")

if not OAUTH_TOKEN:
    print("❌ Error: SOUNDCLOUD_OAUTH_TOKEN environment variable not set.")
    print("")
    print("   To get your token:")
    print("   1. Log into SoundCloud in Chrome")
    print("   2. Open DevTools (F12) → Application → Cookies")
    print("   3. Find 'oauth_token' and copy its value")
    print("")
    print("   Then set it:")
    print("   Windows:   set SOUNDCLOUD_OAUTH_TOKEN=your_token_here")
    print("   Mac/Linux: export SOUNDCLOUD_OAUTH_TOKEN=your_token_here")
    print("   Or create a .env file with: SOUNDCLOUD_OAUTH_TOKEN=your_token_here")
    exit(1)

# Extract user ID from token (format: 2-309337-USERID-xxx)
try:
    USER_ID = OAUTH_TOKEN.split('-')[2]
except:
    print("❌ Error: Could not parse user ID from token.")
    print("   Token format should be: 2-XXXXXX-USERID-XXXX")
    exit(1)

# SoundCloud API endpoints
API_BASE = "https://api-v2.soundcloud.com"

HEADERS = {
    "Authorization": f"OAuth {OAUTH_TOKEN}",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://soundcloud.com",
    "Referer": "https://soundcloud.com/",
}


def get_user_info():
    """Get current user info to verify auth works."""
    url = f"{API_BASE}/me"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Auth failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return None


def get_all_tracks(user_id, limit=200):
    """Fetch all tracks for a user."""
    tracks = []
    url = f"{API_BASE}/users/{user_id}/tracks"
    params = {
        "limit": 50,
        "offset": 0,
        "linked_partitioning": 1,
    }
    
    while True:
        response = requests.get(url, headers=HEADERS, params=params)
        
        if response.status_code != 200:
            print(f"⚠️  Error fetching tracks: {response.status_code}")
            break
        
        data = response.json()
        batch = data.get("collection", [])
        tracks.extend(batch)
        
        print(f"  Fetched {len(tracks)} tracks...", end='\r')
        
        next_href = data.get("next_href")
        if next_href and len(tracks) < limit:
            url = next_href
            params = {}
        else:
            break
    
    print(f"  Fetched {len(tracks)} tracks total")
    return tracks


def format_duration(ms):
    """Convert milliseconds to MM:SS format."""
    if not ms:
        return ""
    seconds = ms // 1000
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


def extract_track_stats(track):
    """Extract relevant stats from track API response."""
    return {
        'title': track.get('title', ''),
        'url': track.get('permalink_url', ''),
        'plays': track.get('playback_count', 0) or 0,
        'likes': track.get('likes_count', 0) or 0,
        'reposts': track.get('reposts_count', 0) or 0,
        'comments': track.get('comment_count', 0) or 0,
        'downloads': track.get('download_count', 0) or 0,
        'upload_date': track.get('created_at', '')[:10] if track.get('created_at') else '',
        'duration': format_duration(track.get('duration')),
        'genre': track.get('genre', ''),
        'tags': track.get('tag_list', ''),
        'description': (track.get('description', '') or '')[:500],
    }


def main():
    print("\n🚀 SoundCloud Metrics Scraper")
    print("=" * 50)
    
    # Verify auth
    print("🔐 Checking authentication...")
    user = get_user_info()
    
    if not user:
        print("\n❌ Authentication failed. Your oauth_token may have expired.")
        print("   Get a fresh token from browser DevTools.")
        return
    
    username = user.get('permalink', 'unknown')
    print(f"👤 Logged in as: {username}")
    print(f"   Followers: {user.get('followers_count', 0):,}")
    print(f"   Tracks: {user.get('track_count', 0)}")
    
    # Fetch all tracks
    print("\n📋 Fetching tracks...")
    tracks = get_all_tracks(USER_ID)
    
    if not tracks:
        print("❌ No tracks found.")
        return
    
    # Extract stats
    print(f"\n📊 Processing {len(tracks)} tracks...")
    all_stats = []
    
    for i, track in enumerate(tracks, 1):
        stats = extract_track_stats(track)
        all_stats.append(stats)
        print(f"  [{i}/{len(tracks)}] {stats['title'][:40]}... ✓ {stats['plays']:,} plays")
    
    # Write CSV
    print(f"\n💾 Writing to {OUTPUT_FILE}...")
    
    fieldnames = ['title', 'url', 'plays', 'likes', 'reposts', 'comments', 
                  'downloads', 'upload_date', 'duration', 'genre', 'tags', 'description']
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_stats)
    
    # Summary
    total_plays = sum(s['plays'] for s in all_stats)
    total_likes = sum(s['likes'] for s in all_stats)
    
    print("\n" + "=" * 50)
    print("✅ COMPLETE!")
    print(f"   Tracks: {len(all_stats)}")
    print(f"   Total plays: {total_plays:,}")
    print(f"   Total likes: {total_likes:,}")
    print(f"   Output: {OUTPUT_FILE}")
    print("=" * 50)
    
    # Also save JSON
    json_file = OUTPUT_FILE.replace('.csv', '.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_stats, f, indent=2, ensure_ascii=False)
    print(f"   Also saved: {json_file}")


if __name__ == "__main__":
    main()
