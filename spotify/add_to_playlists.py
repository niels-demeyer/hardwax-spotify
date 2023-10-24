import base64
import json
from requests import post, get, put
import sys
import os
import psycopg2
import urllib.parse
import time
from search_songs import search_spotify
import time
from datetime import datetime

# Adding the parent directory to the system path to access the config module
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from config import config

conn = psycopg2.connect(
    dbname=config.DB_NAME,
    user=config.DB_USER,
    password=config.DB_PASSWORD,
    host=config.DB_HOST,
    port=config.DB_PORT,
)


print("Connected to database")
cur = conn.cursor()
genres = [
    "ambient",
    "basicChannel",
    "chicago",
    "collectors",
    "colundi",
    "detroit",
    "detroit_house",
    "digital",
    "disco",
    "drexciya",
    "drum_n_bass",
    "electro",
    "essentials",
    "exclusives",
    "grime",
    "honestjons",
    "house",
    "irdial_discs",
    "last_week",
    "mego",
    "new_global_styles",
    "outernational",
    "reggae",
    "reissues",
    "surgeon",
    "techno",
    "this_week",
    "wave",
]

BATCH_SIZE = 100


def get_current_date():
    """Get the current date in YYYY-MM-DD format."""
    return datetime.today().strftime("%Y-%m-%d")


def get_auth_headers(token):
    print("Getting authorization headers...")
    return {"Authorization": "Bearer " + token}


def get_new_access_token(refresh_token):
    """Function to get a new access token using a refresh token."""
    auth_string = config.CLIENT_ID + ":" + config.CLIENT_SECRET
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": config.CLIENT_ID,
        "client_secret": config.CLIENT_SECRET,
    }

    response = post(url, headers=headers, data=data)
    token_json = response.json()
    return token_json.get("access_token", None)


def get_token():
    """Function to get an access token either by refresh token or client credentials."""
    try:
        # First, try to get a new access token using the refresh token
        token = get_new_access_token(config.REFRESH_TOKEN)
        if token:
            print("Token acquired using refresh token.")
            return token

        # If failed, fall back to client credentials flow
        print("Attempting to get Spotify token using client credentials...")
        auth_string = config.CLIENT_ID + ":" + config.CLIENT_SECRET
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"grant_type": "client_credentials"}

        result = post(url, headers=headers, data=data)
        if result.status_code != 200:
            print(f"Failed to get token: {result.status_code} - {result.text}")
            return None

        json_result = json.loads(result.content)
        token = json_result.get("access_token", None)
        if not token:
            print(f"Access token not found in response: {result.content}")
            return None
        print("Token acquired using client credentials.")
        return token

    except Exception as e:
        print(f"Error in getting token: {e}")
        return None


def get_all_genres_from_db(conn):
    with conn.cursor() as cursor:
        cursor.execute("SELECT DISTINCT genre FROM spotify_data_songs")
        return [row[0] for row in cursor.fetchall()]


def get_songs_by_genre(conn, genre):
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT DISTINCT song_id FROM spotify_data_songs WHERE genre = %s",
            (genre,),
        )
        return [row[0] for row in cursor.fetchall()]


def create_playlist_for_genre(genre, token):
    user_id = config.SPOTIFY_USERNAME  # Fetching the Spotify user ID from your config
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    headers = get_auth_headers(token)
    description = (
        f"Last time updated: {get_current_date()}. "
        f"This is a playlist with data scraped from "
        f"https://hardwax.com/. The code can be found https://github.com/niels-demeyer/hardwax-spotify. "
    )
    data = {
        "name": f"Playlist for {genre}",
        "description": description,
        "public": True,
    }
    response = post(url, headers=headers, json=data)
    if response.status_code == 201:
        return response.json().get("id")
    else:
        print(f"Error creating playlist for genre {genre}: {response.status_code}.")
        return None


def update_playlist_description(playlist_id, genre, token):
    """Update the description of a playlist."""
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    headers = get_auth_headers(token)
    description = (
        f"Last time updated: {get_current_date()}. "
        f"This is a playlist with data scraped from "
        f"https://hardwax.com/. The code can be found https://github.com/niels-demeyer/hardwax-spotify. "
    )
    data = {"description": description}
    response = put(url, headers=headers, json=data)  # Using the PUT method to update
    if response.status_code != 200:
        print(
            f"Error updating description for playlist {playlist_id}: {response.status_code}."
        )


def get_tracks_in_playlist(playlist_id, headers):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    all_track_ids = set()

    delay = 0.5  # Initial delay
    max_delay = 60  # Maximum delay
    max_retries = 5  # Maximum retries
    retries = 0  # Initial retry count

    while url and retries < max_retries:
        response = get(url, headers=headers)

        if response.status_code == 200:
            try:
                response_json = response.json()
                items = response_json.get("items", [])
                all_track_ids.update(
                    {item["track"]["id"] for item in items if item.get("track")}
                )
                url = response_json.get("next")  # Check for next page

            except ValueError as e:
                print(f"Error decoding Spotify's JSON response: {e}")
                retries += 1
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                delay = min(max_delay, delay * 2)  # Exponential backoff

        elif response.status_code == 429:
            wait_time = int(response.headers.get("Retry-After", delay))
            print(f"Rate limited! Waiting for {wait_time} seconds...")
            time.sleep(wait_time)
            delay = wait_time  # Update delay to wait time

        else:
            retries += 1
            print(
                f"Error fetching tracks from playlist {playlist_id}: {response.status_code}. Retrying in {delay} seconds..."
            )
            time.sleep(delay)
            delay = min(max_delay, delay * 2)  # Exponential backoff

    if retries >= max_retries:
        print(
            f"Aborted fetching tracks from playlist {playlist_id} after reaching max retries."
        )
        return set(), None

    # Assuming snapshot_id is present in the last response
    snapshot_id = response.json().get("snapshot_id")
    return all_track_ids, snapshot_id


def playlist_exists(genre, user_id, headers):
    """Check if a playlist with the given genre exists for the user."""
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    params = {"limit": 50}  # Spotify allows a maximum of 50 items per request

    while url:
        response = get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            print(response.json())
            return None

        data = response.json()
        for playlist in data.get("items", []):
            if playlist.get("name").strip().lower() == f"playlist for {genre}".lower():
                print(f"Found existing playlist for genre: {genre}")
                return playlist.get("id")

        # Spotify uses paging for large collections. Check if there's another page of playlists.
        url = data.get("next")
        if url:
            print("Checking next page of playlists...")
            time.sleep(1)  # To avoid hitting Spotify's rate limits

    print(f"No existing playlist found for genre: {genre}")
    return None


def add_tracks_to_playlist(playlist_id, track_ids, token, genre, batch_size=100):
    # Define the endpoint URL
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = get_auth_headers(token)

    # Check the current number of tracks in the playlist
    current_track_ids, _ = get_tracks_in_playlist(playlist_id, headers)
    total_tracks = len(current_track_ids)

    print(f"Starting with playlist {playlist_id} which has {total_tracks} tracks.")

    # Split the track IDs into batches
    for i in range(0, len(track_ids), batch_size):
        batched_ids = track_ids[i : i + batch_size]
        remaining_space = 11000 - total_tracks

        print(f"Calculated remaining space: {remaining_space}")
        print(f"Trying to add {len(batched_ids)} tracks.")

        # If the current playlist is reaching its limit, create a new one
        if len(batched_ids) > remaining_space:
            print(
                f"Playlist {playlist_id} is reaching its limit with {remaining_space} remaining space. Creating a new playlist."
            )
            playlist_id = create_playlist_for_genre(genre, token)
            if not playlist_id:
                print(
                    "Failed to create a new playlist. Stopping the addition of tracks."
                )
                return
            total_tracks = 0  # Reset the track count for the new playlist
            url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"  # Update the URL for the new playlist
            print(f"Switched to new playlist: {playlist_id}.")

        # Prepare the data for the request. Spotify expects the track URIs, not just IDs.
        data = {"uris": [f"spotify:track:{track_id}" for track_id in batched_ids]}

        # Make the request
        response = post(url, headers=headers, json=data)

        # Handle the response
        if response.status_code == 201:
            total_tracks += len(batched_ids)
            print(
                f"Successfully added {len(batched_ids)} tracks to playlist {playlist_id}."
            )
        else:
            print(
                f"Failed to add tracks to playlist {playlist_id}. Status code: {response.status_code}. Message: {response.text}."
            )


def main():
    print("starting script...")

    # obtain the access token
    token = get_token()

    if not token:
        print("Couldn't obtain token. Exiting.")
        return  # Exiting function if token is not obtained

    # working with predefined genres
    print(f"Working with {len(genres)} predefined genres.")

    for genre in genres:
        # check if a playlist for this genre exists
        playlist_id = playlist_exists(
            genre, config.SPOTIFY_USERNAME, get_auth_headers(token)
        )
        if playlist_id:
            print(f"Playlist for genre: {genre} already exists. Using it.")
        else:
            print(f"No existing playlist found for genre: {genre}. Creating one.")
            playlist_id = create_playlist_for_genre(genre, token)
            if not playlist_id:
                print(f"Couldn't create a playlist for genre: {genre}. Skipping.")
                continue  # This will now work as it's within the for loop
            print(f"Successfully created playlist for genre: {genre}")

        # fetching song IDs for the given genre
        print(f"Fetching songs for genre {genre}")
        song_ids = get_songs_by_genre(conn, genre)
        print(f"Fetched {len(song_ids)} songs for genre {genre}")
        existing_tracks_in_playlist, snapshot_id = get_tracks_in_playlist(
            playlist_id, get_auth_headers(token)
        )
        print(
            f"Found {len(existing_tracks_in_playlist)} existing tracks in the playlist for genre: {genre}"
        )
        all_track_ids = get_songs_by_genre(conn, genre)

        print(f"Fetched total of {len(all_track_ids)} tracks for genre: {genre}")

        new_tracks_to_add = set(all_track_ids) - set(
            existing_tracks_in_playlist
        )  # Assuming these are sets

        if new_tracks_to_add:
            print(
                f"Adding {len(new_tracks_to_add)} new tracks to playlist for genre: {genre}"
            )
            add_tracks_to_playlist(playlist_id, list(new_tracks_to_add), token, genre)
            print(f"Successfully added new tracks to playlist for genre: {genre}")
        else:
            print(f"No new tracks to add for genre: {genre}")

        # Always update the playlist description regardless of new tracks being added or not
        update_playlist_description(playlist_id, genre, token)
        print(f"Successfully updated playlist description for genre: {genre}")


if __name__ == "__main__":
    main()
