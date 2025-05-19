import streamlit as st
import requests
import base64
import pandas as pd
import datetime
import urllib.parse
import plotly.express as px
import pydeck as pdk

# --- App configuration ---
st.set_page_config(page_title="StreamLive", layout="wide")

st.image("logo_streamlive.jpg", width=300)

st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    .app-title { font-size: 2.2em; font-weight: bold; color: #4A4A4A; }
    div[data-testid="stMetric"] {
        background-color: #f0f0f5;
        padding: 10px;
        border-radius: 10px;
        margin: 5px;
    }
    summary { font-size: 1.1rem; }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.markdown("<h1 class='app-title'>Find Live Shows from Your Spotify Playlists</h1>", unsafe_allow_html=True)

# --- Inputs in the Side Bar ---
with st.sidebar:
    st.header("🔍 Search Options")
    playlist_url = st.text_input("Playlist URL (Make sure it's created by a user and public)")
    city = st.text_input("City (optional)")
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
        with st.spinner("🎵 Fetching playlist and concert data..."):
            try:
                playlist_id = playlist_url.split("playlist/")[1].split("?")[0]
                res_tracks = requests.get(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", headers=headers)
                tracks_data = res_tracks.json()

                items = tracks_data.get("items", [])
                if not items:
                    st.warning("🚫 The playlist appears to be empty.")
                else:
                    artists = []
                    artist_ids = []
                    for item in items:
                        artist = item["track"]["artists"][0]
                        name = artist["name"]
                        artist_id = artist["id"]
                        if name not in artists:
                            artists.append(name)
                            artist_ids.append(artist_id)

                    concert_counts = {}
                    map_data = []
                    scatter_data = []

                    for name, artist_id in zip(artists, artist_ids):
                        params = {
                            "apikey": TICKETMASTER_API_KEY,
                            "keyword": name,
                            "startDateTime": start_date.isoformat() + "T00:00:00Z",
                            "endDateTime": end_date.isoformat() + "T23:59:59Z",
                            "size": 5
                        }
                        if city.strip():
                            params["city"] = city.strip()

                        response = requests.get("https://app.ticketmaster.com/discovery/v2/events.json", params=params)
                        events = response.json().get("_embedded", {}).get("events", [])

                        if not events:
                            continue

                        concert_counts[name] = len(events)

                        artist_info = requests.get(f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers).json()
                        popularity = artist_info.get("popularity", 0)
                        followers = artist_info.get("followers", {}).get("total", 0)
                        genres = artist_info.get("genres", [])

                        scatter_data.append({"artist": name, "popularity": popularity, "concerts": len(events)})

                        with st.expander(f"🎤 {name} – {len(events)} Concert(s)"):
                            cols = st.columns(3)
                            cols[0].metric("Popularity", f"{popularity}/100")
                            cols[1].metric("Followers", f"{followers:,}")
                            cols[2].write(f"**Genres:** {', '.join(genres) if genres else 'N/A'}")

                            st.markdown("---")

                            for event in events:
                                venue_info = event.get("_embedded", {}).get("venues", [{}])[0]
                                venue = venue_info.get("name", "Venue N/A")
                                city_name = venue_info.get("city", {}).get("name", "City N/A")
                                country_name = venue_info.get("country", {}).get("name", "Country N/A")
                                date = event["dates"]["start"].get("localDate", "Date N/A")
                                event_name = event["name"]
                                start_iso = event["dates"]["start"].get("dateTime", "")

                                try:
                                    formatted_date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%b %d, %Y")
                                except:
                                    formatted_date = date

                                st.markdown(f"{event_name}")
                                st.write(f"📍 Venue: {venue} – {city_name}, {country_name}")
                                st.write(f"📅 Date: {formatted_date}")

                                if start_iso:
                                    start_google = start_iso.replace("-", "").replace(":", "").replace("Z", "Z")
                                    calendar_link = f"https://www.google.com/calendar/render?action=TEMPLATE&text={urllib.parse.quote(event_name)}&dates={start_google}/{start_google}"
                                    st.markdown(f"[🗓 Add to Google Calendar]({calendar_link})")

                                st.markdown("---")

                                latlon = venue_info.get("location", {})
                                if "latitude" in latlon and "longitude" in latlon:
                                    map_data.append({
                                        "lat": float(latlon["latitude"]),
                                        "lon": float(latlon["longitude"]),
                                        "event": event_name
                                    })

                    # --- Visualizations ---
                    if concert_counts:
                        st.subheader("Concerts per Artist")
                        df_bar = pd.DataFrame(list(concert_counts.items()), columns=["Artist", "Concerts"])
                        fig_bar = px.bar(df_bar, x="Artist", y="Concerts", title="Number of Concerts", height=400)
                        st.plotly_chart(fig_bar, use_container_width=True)

                    if scatter_data:
                        st.subheader("Popularity vs. Number of Concerts")
                        df_scatter = pd.DataFrame(scatter_data)
                        fig_scatter = px.scatter(
                            df_scatter,
                            x="popularity",
                            y="concerts",
                            hover_name="artist",
                            color="artist",  
                            size="concerts",
                            title="Artist Popularity vs. Concert Count",
                            height=450
                        )
                        fig_scatter.update_layout(legend_title="Artist")
                        st.plotly_chart(fig_scatter, use_container_width=True)

                    if map_data:
                        st.subheader("Concert Map")
                        df_map = pd.DataFrame(map_data)
                        layer = pdk.Layer("ScatterplotLayer",
                                        data=df_map,
                                        get_position='[lon, lat]',
                                        get_radius=70000,
                                        get_fill_color=[200, 30, 0, 160])
                        view_state = pdk.ViewState(latitude=df_map["lat"].mean(),
                                                longitude=df_map["lon"].mean(),
                                                zoom=2)
                        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))

                    if not concert_counts:
                        st.info("No concerts found for the artists in this playlist in the selected city or date range.")

            except Exception as e:
                st.error(f"An error occurred: {e}")
