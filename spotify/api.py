import base64
import json
from requests import post, get, put
import psycopg2
import time
from datetime import datetime
from psycopg2 import sql
from dotenv import load_dotenv
import os

env_path = r"../config/.env"
load_dotenv(env_path)

DB_NAME = "hardwax_spotify"
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
SPOTIFY_USERNAME = os.getenv("SPOTIFY_USERNAME")

conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
)


print("Connected to database")
cur = conn.cursor()


BATCH_SIZE = 100


def get_current_date():
    """Get the current date in YYYY-MM-DD format."""
    return datetime.today().strftime("%Y-%m-%d")


def get_auth_headers(token):
    print("Getting authorization headers...")
    return {"Authorization": "Bearer " + token}


def get_new_access_token(refresh_token):
    """Function to get a new access token using a refresh token."""
    auth_string = CLIENT_ID + ":" + CLIENT_SECRET
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
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    response = post(url, headers=headers, data=data)
    token_json = response.json()
    return token_json.get("access_token", None)


def get_token():
    """Function to get an access token either by refresh token or client credentials."""
    try:
        # First, try to get a new access token using the refresh token
        token = get_new_access_token(REFRESH_TOKEN)
        if token:
            print("Token acquired using refresh token.")
            return token

        # If failed, fall back to client credentials flow
        print("Attempting to get Spotify token using client credentials...")
        auth_string = CLIENT_ID + ":" + CLIENT_SECRET
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


def get_table_names(conn):
    """Get a list of table names from the database, excluding 'playlist_ids'."""
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema='public' AND table_catalog='hardwax_spotify' AND table_name != 'playlist_ids'
            """
        )
        tables = cursor.fetchall()
        return [table[0] for table in tables]


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


def ensure_playlist_table_exists(conn):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS playlist_ids (
                id SERIAL PRIMARY KEY,
                genre VARCHAR(255) NOT NULL,
                playlist_id VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            );
            """
        )
        cursor.execute(
            """
            SELECT 1
            FROM pg_constraint
            WHERE conname = 'unique_genre'
            """
        )
        if cursor.fetchone() is None:
            cursor.execute(
                "ALTER TABLE playlist_ids ADD CONSTRAINT unique_genre UNIQUE (genre);"
            )
        conn.commit()
        print("Checked and ensured playlist_ids table exists.")


def populate_playlist_ids_table(conn, genres, spotify_token):
    """Create Spotify playlists for each genre and store the information in the playlist_ids table."""
    with conn.cursor() as cursor:
        for genre in genres:
            playlist_id = create_spotify_playlist(
                genre, spotify_token
            )  # Replace with your actual function call
            cursor.execute(
                """
                INSERT INTO playlist_ids (genre, playlist_id) VALUES (%s, %s)
                ON CONFLICT (genre) DO UPDATE SET playlist_id = EXCLUDED.playlist_id
            """,
                (genre, playlist_id),
            )
        conn.commit()


def get_playlist_tracks(playlist_id, token):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = get_auth_headers(token)
    track_uris = []

    while url:
        response = get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            track_uris.extend(item["track"]["uri"] for item in items if "track" in item)
            url = data.get("next")
        else:
            print(
                f"Failed to get tracks from playlist {playlist_id}: {response.status_code} - {response.text}"
            )
            break

    return track_uris


def add_tracks_to_playlist(playlist_id, track_ids, token):
    existing_track_uris = set(get_playlist_tracks(playlist_id, token))
    track_uris_to_add = [
        f"spotify:track:{track_id}"
        for track_id in track_ids
        if f"spotify:track:{track_id}" not in existing_track_uris
    ]

    if not track_uris_to_add:
        print("All tracks are already in the playlist.")
        return

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = get_auth_headers(token)
    max_retries = 3
    delay = 1  # in seconds

    for i in range(0, len(track_uris_to_add), BATCH_SIZE):
        batch = track_uris_to_add[i : i + BATCH_SIZE]
        data = {"uris": batch}

        retries = 0
        while retries < max_retries:
            response = post(url, headers=headers, json=data)
            if response.status_code == 201:
                print(f"Added {len(batch)} tracks to playlist {playlist_id}")
                break
            elif response.status_code in [500, 502]:
                print(
                    f"Failed to add tracks to playlist {playlist_id}: {response.status_code} - {response.text}. Retrying in {delay} seconds..."
                )
                time.sleep(delay)
                retries += 1
                delay *= 2  # Exponential backoff
            else:
                print(
                    f"Failed to add tracks to playlist {playlist_id}: {response.status_code} - {response.text}"
                )
                break


def get_track_ids_for_genre(conn, genre):
    query = sql.SQL("SELECT song_id FROM {}").format(sql.Identifier(genre))
    with conn.cursor() as cursor:
        cursor.execute(query)
        track_ids = cursor.fetchall()
        return [track_id[0] for track_id in track_ids]


def create_spotify_playlist(genre, token):
    """
    Create a Spotify playlist for a given genre.

    :param genre: The genre of the playlist
    :param token: Spotify API access token
    :return: The Spotify playlist ID
    """
    # Define the Spotify API endpoint for creating a new playlist
    url = f"https://api.spotify.com/v1/users/{SPOTIFY_USERNAME}/playlists"

    # Define the headers including the authorization token
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Define the playlist creation data
    data = {
        "name": f"{genre} Playlist",
        "description": f"A playlist of {genre} genre",
        "public": True,  # Set to True if you want the playlist to be public
    }

    # Make the API request to create the playlist
    response = post(url, headers=headers, data=json.dumps(data))

    # Check if the playlist was created successfully
    if response.status_code == 201:
        playlist_id = response.json().get("id")
        print(f"Playlist for {genre} created successfully. Playlist ID: {playlist_id}")
        return playlist_id
    else:
        print(
            f"Failed to create playlist for {genre}. Status Code: {response.status_code}. Response: {response.text}"
        )
        return None


def create_and_store_playlists(cur, genres, token):
    for genre in genres:
        # Check if playlist for genre already exists
        cur.execute("SELECT playlist_id FROM playlist_ids WHERE genre = %s", (genre,))
        result = cur.fetchone()

        if result:
            playlist_id = result[0]
            print(f"Playlist for {genre} already exists. Playlist ID: {playlist_id}")
        else:
            # If playlist does not exist, create a new playlist
            playlist_id = create_spotify_playlist(genre, token)
            if not playlist_id:
                print(f"Failed to create playlist for {genre}")
                continue
            print(f"Created new playlist for {genre}. Playlist ID: {playlist_id}")

            # Store new playlist ID in the database
            cur.execute(
                """
                INSERT INTO playlist_ids (genre, playlist_id) VALUES (%s, %s)
                ON CONFLICT (genre) DO UPDATE SET playlist_id = EXCLUDED.playlist_id, updated_at = CURRENT_TIMESTAMP
                """,
                (genre, playlist_id),
            )

        # Update playlist description
        update_playlist_description(playlist_id, genre, token)

        # Get track IDs for the genre
        track_ids = get_track_ids_for_genre(cur.connection, genre)

        # Add tracks to the playlist
        add_tracks_to_playlist(playlist_id, track_ids, token)

        print(f"Tracks added and description updated for {genre} playlist.")


def main():
    # Ensure the necessary table exists
    ensure_playlist_table_exists(conn)

    # Get Spotify token
    token = get_token()
    if not token:
        print("Failed to get Spotify token")
        return

    # Get table names as genres
    genres = get_table_names(conn)
    if not genres:
        print("No genres found")
        return

    # Create playlists and store in the database
    with conn.cursor() as cursor:
        create_and_store_playlists(cursor, genres, token)

    # Commit changes and close database connection
    conn.commit()
    conn.close()
    print("Database connection closed")


if __name__ == "__main__":
    main()
