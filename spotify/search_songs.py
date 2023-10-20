import base64
import json
from requests import post, get
import sys
import os
import psycopg2
import urllib.parse
import time
from fuzzywuzzy import fuzz


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


def get_auth_headers(token):
    print("Getting authorization headers...")
    return {"Authorization": "Bearer " + token}


def get_token():
    try:
        print("Attempting to get Spotify token...")

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

        try:
            json_result = json.loads(result.content)
            print(result.content)
            token = json_result.get("access_token", None)
            if not token:
                print(f"Access token not found in response: {result.content}")
            print(f"Token acquired: {token}")
            return token
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON response: {e}")
            print(f"Response content: {result.content}")

    except Exception as e:
        print(f"Error in getting token: {e}")


def search_spotify(item_type, query, artist_name, headers):
    base_url = "https://api.spotify.com/v1/search"
    params = {"q": f"{query} artist:{artist_name}", "type": item_type, "limit": 5}

    delay = 0.5
    max_delay = 60
    max_retries = 5
    retries = 0

    while retries < max_retries:
        response = get(base_url, headers=headers, params=params)

        if response.status_code == 200:
            try:
                data = response.json()
                if not isinstance(data, dict):
                    raise ValueError("Unexpected data format from Spotify.")
                results = data.get(item_type + "s", {}).get("items", [])
                return results if results else None

            except json.JSONDecodeError:
                raise ValueError(
                    "Error decoding Spotify's JSON response. Might not be JSON format."
                )

        elif response.status_code == 429:
            wait_time = int(response.headers.get("Retry-After", delay))
            print(f"Rate limited! Waiting for {wait_time} seconds...")
            time.sleep(wait_time)
            delay = wait_time

        elif response.status_code in [400, 401, 404]:
            raise ValueError(f"Error {response.status_code}: {response.text}")

        else:
            retries += 1
            print(
                f"Error searching for {item_type} '{query}' on Spotify: {response.status_code}. Retrying in {delay} seconds..."
            )
            time.sleep(delay)
            delay = min(max_delay, delay * 2)

    raise ValueError(
        f"Aborted search for {item_type} '{query}' after reaching max retries."
    )


def create_spotify_data_table():
    try:
        print("Attempting to create spotify_data_songs table...")
        create_table_query = """
        CREATE TABLE IF NOT EXISTS spotify_data_songs (
            id SERIAL PRIMARY KEY,
            genre VARCHAR(255),
            artist VARCHAR(255),
            song VARCHAR(255),
            album VARCHAR(255),
            artist_id VARCHAR(255),
            song_id VARCHAR(255),
            album_id VARCHAR(255),
            UNIQUE(genre, artist, song)
        );
        """
        cur.execute(create_table_query)
        conn.commit()
        print("Table spotify_data_songs ensured to exist successfully")
    except Exception as e:
        print(f"Error in creating table: {e}")


def search_and_store_spotify_data(genre, artist, song, headers, album):
    results = search_spotify("track", song, artist, headers)

    if not results:
        print(f"No match found for song '{song}' by artist '{artist}'.")
        return

    best_match = find_best_match(artist, song, album, results)

    if best_match:
        artist_id = (
            best_match["artists"][0]["id"]
            if best_match and "artists" in best_match and best_match["artists"]
            else None
        )
        song_id = best_match["id"] if best_match and "id" in best_match else None
        album_id = (
            best_match["album"]["id"]
            if "album" in best_match and "id" in best_match["album"]
            else None
        )

        if not artist_id or not song_id or not album_id:
            print(
                f"Unexpected data structure for best_match: {best_match}. Skipping entry."
            )
            return

        try:
            cur.execute(
                """
                INSERT INTO spotify_data_songs (genre, artist, song, album, artist_id, song_id, album_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (genre, artist, song) DO NOTHING;
                """,
                (
                    genre,
                    artist,
                    song,
                    album,
                    artist_id,
                    song_id,
                    album_id,
                ),
            )
            conn.commit()
            print(
                f"Successfully stored data for song '{song}' by artist '{artist}' into the database."
            )
        except psycopg2.IntegrityError:
            conn.rollback()
            print(f"Duplicate entry detected: {genre}, {artist}, {song}. Skipping.")
    else:
        print(f"No matching artist-song combination found for {artist} - {song}")


def get_last_processed_artist_song(genre):
    cur.execute(
        """
        SELECT artist, song
        FROM spotify_data_songs  
        WHERE genre = %s 
        ORDER BY id DESC 
        LIMIT 1;
    """,
        (genre,),
    )
    result = cur.fetchone()
    if result:
        return result
    return None, None


def find_best_match(artist, song, album, results):
    best_match = None
    best_score = -1

    for idx, result in enumerate(results):
        # Ensure the structure of the result is as expected
        if not (
            isinstance(result, dict)
            and "artists" in result
            and isinstance(result["artists"], list)
            and result["artists"]
        ):
            print(
                f"DEBUG - Skipping result {idx} due to unexpected structure. Actual structure: {result}"
            )
            continue

        artist_similarity = fuzz.ratio(artist, result["artists"][0]["name"])
        song_similarity = fuzz.ratio(song, result["name"])

        # print(f"DEBUG - Result {idx} artist similarity: {artist_similarity}")
        # print(f"DEBUG - Result {idx} song similarity: {song_similarity}")

        if artist_similarity > 80 and song_similarity > 80:
            current_score = artist_similarity + song_similarity

            if (
                album
                and "album" in result
                and isinstance(result["album"], dict)
                and result["album"].get("name") == album
            ):  # Enhanced check
                current_score += 10
                # print(f"DEBUG - Result {idx} matched album, boosting score.")

            print(f"DEBUG - Result {idx} current score: {current_score}")

            if current_score > best_score:
                best_score = current_score
                best_match = result
        else:
            print(f"DEBUG - Result {idx} discarded due to low similarity.")

    return best_match


def main():
    try:
        # Ensure the spotify_data_songs table exists before any operations.
        print("Ensuring spotify_data_songs table exists...")
        create_spotify_data_table()

        # Fetch the Spotify token.
        print("Fetching the token from Spotify...")
        token = get_token()
        if not token:
            print("Could not obtain token. Exiting...")
            return

        headers = get_auth_headers(token)

        # Process each genre.
        for genre in genres:
            print(f"Processing genre: {genre}")

            # Fetch the last processed artist and song for the current genre.
            last_processed_artist, last_processed_song = get_last_processed_artist_song(
                genre
            )

            # Fetch artist and song details from your database.
            cur.execute(
                f"""
                SELECT m.artist, m.project_title, s.song_title 
                FROM {genre}_music AS m
                JOIN {genre}_songs AS s ON m.id = s.{genre}_music_id
                ORDER BY m.artist, s.song_title
                """
            )

            artist_song_mappings = cur.fetchall()

            start_processing = False
            if not last_processed_artist and not last_processed_song:
                start_processing = (
                    True  # If there's no last processed item, process all.
                )

            for mapping in artist_song_mappings:
                artist, album, song = mapping

                # Start processing from the last processed item.
                if not start_processing:
                    if artist == last_processed_artist and song == last_processed_song:
                        start_processing = True
                    continue

                search_and_store_spotify_data(genre, artist, song, headers, album)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        print("Database connection closed")


if __name__ == "__main__":
    main()
