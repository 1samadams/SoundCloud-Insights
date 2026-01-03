# SoundCloud Dashboard

Flask-based dashboard for visualizing your SoundCloud geographic data.

## Setup

1. Generate data first by running `soundcloud_insights.py` from the parent directory
2. Copy the data file here: `cp ../soundcloud_insights.json .`
3. Run: `python app.py`
4. Open: http://localhost:5000

## Features

- Interactive world map with city markers
- Drill-down: Track → Countries → Cities
- Reverse lookup: Country → Tracks
- Breadcrumb navigation
