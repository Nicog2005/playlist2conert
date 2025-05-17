import streamlit as st
import requests
import base64
import pandas as pd
import datetime
import urllib.parse

st.title("Find Concerts and Songs from Spotify Playlists")

# --- Inputs ---
playlist_url = st.text_input("Enter a Spotify playlist URL")
city = st.text_input("Enter a city (optional)")
start_date = st.date_input("Start date", datetime.date.today())
end_date = st.date_input("End date", datetime.date.today() + datetime.timedelta(days=90))

# --- API Keys ---
TICKETMASTER_API_KEY = st.secrets["TICKETMASTER_API_KEY"]
SPOTIFY_CLIENT_ID = st.secrets["SPOTIFY_CLIENT_ID"]
SPOTIFY_CLIENT_SECRET = st.secrets["SPOTIFY_CLIENT_SECRET"]

# --- Spotify Token ---
auth = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
b64_auth = base64.b64encode(auth.encode()).decode()
headers_spotify = {"Authorization": f"Basic {b64_auth}"}
data = {"grant_type": "client_credentials"}
res_token = requests.post("https://accounts.spotify.com/api/token", headers=headers_spotify, data=data)
token = res_token.json().get("access_token")

if not token:
    st.error("Error getting Spotify token.")
else:
    headers = {"Authorization": f"Bearer {token}"}

    if playlist_url:
        try:
            playlist_id = playlist_url.split("playlist/")[1].split("?")[0]
            res_tracks = requests.get(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", headers=headers)
            tracks_data = res_tracks.json()

            artists = []
            artist_ids = []
            for item in tracks_data.get("items", []):
                artist = item["track"]["artists"][0]
                name = artist["name"]
                artist_id = artist["id"]
                if name not in artists:
                    artists.append(name)
                    artist_ids.append(artist_id)

            concert_counts = {}
            map_data = []
            scatter_data = []

            # Process artists who have concerts
            for name, artist_id in zip(artists, artist_ids):
                params = {
                    "apikey": TICKETMASTER_API_KEY,
                    "keyword": name,
                    "city": city,
                    "startDateTime": start_date.isoformat() + "T00:00:00Z",
                    "endDateTime": end_date.isoformat() + "T23:59:59Z",
                    "size": 5
                }
                url_events = "https://app.ticketmaster.com/discovery/v2/events.json"
                response = requests.get(url_events, params=params)
                events = response.json().get("_embedded", {}).get("events", [])

                if not events:
                    continue  # Skip artists with no concerts

                concert_counts[name] = len(events)

                # Spotify artist info
                artist_info = requests.get(f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers).json()
                popularity = artist_info.get("popularity", 0)
                followers = artist_info.get("followers", {}).get("total", 0)
                genres = artist_info.get("genres", [])

                scatter_data.append({"artist": name, "popularity": popularity, "concerts": len(events)})

                # Improved display starts here
                with st.expander(f"{name} - {len(events)} Upcoming Concert(s)"):
                    cols = st.columns([2, 2, 4])
                    cols[0].metric("Popularity", f"{popularity}/100")
                    cols[1].metric("Followers", f"{followers:,}")
                    cols[2].write(f"**Genres:** {', '.join(genres) if genres else 'N/A'}")

                    st.markdown("---")

                    for event in events:
                        venue = event["_embedded"]["venues"][0]["name"]
                        date = event["dates"]["start"].get("localDate", "Date N/A")
                        event_name = event["name"]
                        start_iso = event['dates']['start'].get('dateTime', '')

                        # Format date nicely
                        try:
                            formatted_date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%b %d, %Y")
                        except:
                            formatted_date = date

                        st.markdown(f"**🎤 {event_name}**  ")
                        st.write(f"📍 Venue: {venue}  ")
                        st.write(f"📅 Date: {formatted_date}")

                        if start_iso:
                            start_google = start_iso.replace("-", "").replace(":", "").replace("Z", "Z")
                            calendar_link = f"https://www.google.com/calendar/render?action=TEMPLATE&text={urllib.parse.quote(event_name)}&dates={start_google}/{start_google}"
                            st.markdown(f"[Add to Google Calendar]({calendar_link})")

                        st.markdown("---")

                        # Map info
                        latlon = event["_embedded"]["venues"][0].get("location", {})
                        if "latitude" in latlon and "longitude" in latlon:
                            map_data.append({
                                "lat": float(latlon["latitude"]),
                                "lon": float(latlon["longitude"]),
                                "event": event_name
                            })

            # Bar chart: concerts per artist
            if concert_counts:
                st.subheader("Concert Count per Artist")
                df_bar = pd.DataFrame(list(concert_counts.items()), columns=["Artist", "Concerts"])
                st.bar_chart(df_bar.set_index("Artist"))

            # Scatter plot: popularity vs concerts
            if scatter_data:
                st.subheader("Popularity vs. Number of Concerts")
                df_scatter = pd.DataFrame(scatter_data)
                st.scatter_chart(df_scatter.rename(columns={"artist": "index"}).set_index("index"))

            # Map view
            if map_data:
                st.subheader("Concert Locations")
                df_map = pd.DataFrame(map_data)
                st.map(df_map)

        except Exception as e:
            st.error(f"An error occurred: {e}")
