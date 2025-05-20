# Playlist2Concert: Discover Concerts from Spotify Playlists

This Streamlit app lets users input a Spotify playlist and a city to:
- Find upcoming concerts by the artists in the playlist.
- Visualize popularity vs number of concerts.
- Add events to Google Calendar.
- See concert locations on a map.
- Get alerts if no concerts are found.
- Watch for a loading spinner while data is processed.
- Receive email with concert information

---

## Live Demo

https://playlist2concert.streamlit.app/  

---

## Requirements

- streamlit
- requests
- pandas
- plotly
- pydeck

## Secrets Configuration

Create a .streamlit/secrets.toml file to store your API keys:

""
- TICKETMASTER_API_KEY = "your_ticketmaster_key"
- SPOTIFY_CLIENT_ID = "your_spotify_client_id"
- SPOTIFY_CLIENT_SECRET = "your_spotify_client_secret"

""

## Running Locally

- streamlit run prueba.py

## Project Structure

```plaintext
playlist2concert/
├── prueba.py                 # Main Streamlit app
├── requirements.txt          # Dependencies
└── .streamlit/
    └── secrets.toml          # (Local only) API keys
