import base64
import json
from requests import post, get
import os
from dotenv import load_dotenv
import psycopg2
import time
from fuzzywuzzy import fuzz
from typing import List, Optional, Dict, Any
import pprint

env_path = r"../config/.env"
load_dotenv(env_path)

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
)

print("Connected to database")
cur = conn.cursor()

# genres = [
#     "ambient",
#     "basicChannel",
#     "chicago",
#     "collectors",
#     "colundi",
#     "detroit",
#     "detroit_house",
#     "digital",
#     "disco",
#     "drexciya",
#     "drum_n_bass",
#     "electro",
#     "essentials",
#     "exclusives",
#     "grime",
#     "honestjons",
#     "house",
#     "irdial_discs",
#     "last_week",
#     "mego",
#     "new_global_styles",
#     "outernational",
#     "reggae",
#     "reissues",
#     "surgeon",
#     "techno",
#     "this_week",
#     "wave",
# ]


def get_auth_headers(token):
    print("Getting authorization headers...")
    return {"Authorization": "Bearer " + token}


def get_token():
    try:
        print("Attempting to get Spotify token...")

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


def ensure_spotify_data_table_exists():
    try:
        print("Ensuring spotify_data_songs table exists...")
        cur.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'spotify_data_songs'
            );
            """
        )
        result = cur.fetchone()
        if result[0]:
            print("Table spotify_data_songs exists")
            return True
        else:
            create_spotify_data_table()
    except Exception as e:
        print(f"Error in ensuring table exists: {e}")


###the old way
# def get_genre_music(cur):
#     try:
#         cur.execute(
#             """
#             SELECT genre, artist, project_title, track
#             FROM all_results
#             ORDER BY genre, artist, project_title, track
#             """
#         )
#         genre_music = cur.fetchall()
#         return genre_music
#     except Exception as e:
#         print(f"Error in getting genre music: {e}")


def get_music_albums(cur):
    try:
        cur.execute(
            """
            SELECT genre, artist, album, track
            FROM music_albums
            ORDER BY genre, artist, album, track
            """
        )
        genre_music = cur.fetchall()
        return genre_music
    except Exception as e:
        print(f"Error in getting genre music: {e}")


def get_genre_music_albums(cur, genre):
    # # Replace hyphens with underscores in the genre name
    # genre = genre.replace("-", "_")
    try:
        cur.execute(
            """
            SELECT genre, artist, album, track
            FROM music_albums
            WHERE genre = %s
            ORDER BY genre, artist, album, track
            """,
            (genre,),
        )
        genre_music = cur.fetchall()
        print(f"Genre music: {len(genre_music)}")

        return genre_music
    except Exception as e:
        print(f"Error in getting genre music: {e}")


def get_spotify_data_songs(cur):
    try:
        cur.execute(
            """
            SELECT genre, artist, album, song
            FROM spotify_data_songs
            ORDER BY genre, artist, album, song
            """
        )
        spotify_data_songs = cur.fetchall()
        return spotify_data_songs
    except Exception as e:
        print(f"Error in getting spotify data songs: {e}")


def get_not_results(cur):
    try:
        cur.execute(
            """
            SELECT genre, artist, song
            FROM not_results
            ORDER BY genre, artist, song
            """
        )
        not_results = cur.fetchall()
        return not_results
    except Exception as e:
        print(f"Error in getting not results: {e}")


def create_not_results_table(cur, conn):
    try:
        print("Attempting to create not_results table...")
        create_table_query = """
        CREATE TABLE IF NOT EXISTS not_results (
            id SERIAL PRIMARY KEY,
            genre VARCHAR(255),
            artist VARCHAR(255),
            song VARCHAR(255),
            UNIQUE(genre, artist, song)
        );
        """
        cur.execute(create_table_query)
        conn.commit()
        print("Table not_results ensured to exist successfully")
    except Exception as e:
        print(f"Error in creating table: {e}")


# def get_unique_genre_music(cur, genres, specific_genre=None):
#     # Existing function calls
#     genre_music_list = get_genre_music(cur)
#     spotify_data_songs = get_spotify_data_songs(cur)
#     not_results_list = get_not_results(cur)

#     print(f"Genre music list: {len(genre_music_list)}")
#     print(f"Spotify data songs: {len(spotify_data_songs)}")
#     print(f"Not results list: {len(not_results_list)}")

#     # Convert spotify_data_songs to a set of (album, song) for faster lookup
#     spotify_data_songs_set = set((song[2], song[3]) for song in spotify_data_songs)
#     not_results_set = set((song[1], song[2]) for song in not_results_list)

#     unique_genre_music = []
#     unique_not_results = []

#     # Check each item in genre_music_list for unique (album, song) combination
#     for song in genre_music_list:
#         album_song_pair = (song[2], song[3])
#         if album_song_pair not in spotify_data_songs_set:
#             unique_genre_music.append(song)

#     for song in unique_genre_music:
#         album_song_pair = (song[1], song[3])
#         if album_song_pair not in not_results_set:
#             unique_not_results.append(song)

#     return unique_not_results


def get_unique_genre_music(cur, genre=None):
    try:
        # Existing function calls
        if genre:
            music_albums = set(get_genre_music_albums(cur, genre))
        else:
            music_albums = set(get_music_albums(cur))
        spotify_data_songs = set(get_spotify_data_songs(cur))
        not_results_set = set(get_not_results(cur))

        print(f"Music albums: {len(music_albums)}")
        print(f"Spotify data songs: {len(spotify_data_songs)}")
        print(f"Not results list: {len(not_results_set)}")
        print(f"First music album: {next(iter(music_albums), 'No music albums')}")
        print(
            f"First Spotify data song: {next(iter(spotify_data_songs), 'No Spotify data songs')}"
        )
        print(f"First not result: {next(iter(not_results_set), 'No not results')}")

        unique_music_albums = music_albums - spotify_data_songs - not_results_set
        print(f"Unique music albums: {len(unique_music_albums)}")
        if unique_music_albums:
            print(
                f"First unique music album: {next(iter(unique_music_albums), 'No unique music albums')}"
            )
        return unique_music_albums
    except Exception as e:
        print(f"Error in getting unique genre music: {e}")


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


def create_not_results_table(cur, conn):
    try:
        print("Attempting to create not_results table...")
        create_table_query = """
        CREATE TABLE IF NOT EXISTS not_results (
            id SERIAL PRIMARY KEY,
            genre VARCHAR(255),
            artist VARCHAR(255),
            song VARCHAR(255),
            UNIQUE(genre, artist, song)
        );
        """
        cur.execute(create_table_query)
        conn.commit()
        print("Table not_results ensured to exist successfully")
    except Exception as e:
        print(f"Error in creating table: {e}")


def check_table_exists(cur, table_name):
    cur.execute(
        f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE  table_name = '{table_name}'
        );
    """
    )
    return cur.fetchone()[0]


def not_results(genre, artist, song):
    try:
        if not check_table_exists(cur, "not_results"):
            create_not_results_table(cur, conn)  # Ensure table exists
        cur.execute(
            """
            INSERT INTO not_results (genre, artist, song)
            VALUES (%s, %s, %s)
            ON CONFLICT (genre, artist, song) DO NOTHING;
            """,
            (
                genre,
                artist,
                song,
            ),
        )
        conn.commit()
        print(
            f'Successfully stored song "{song}" by artist "{artist}" into the not_results TABLE.'
        )
    except psycopg2.IntegrityError:
        conn.rollback()
        print(f"Duplicate entry detected: {genre}, {artist}, {song}. Skipping.")
    except Exception as e:
        print(f"Error in storing not results: {e}")


def search_and_store_spotify_data(genre, artist, song, headers, album):
    # If artist is 'Various Artists', pass an empty string for artist parameter in search_spotify function
    if artist.lower() == "various artists":
        results = search_spotify("track", f"{song} album:{album}", "", headers)
    else:
        results = search_spotify("track", song, artist, headers)

    if not results:
        print(f"No match found for song '{song}' by artist '{artist}'.")
        not_results(genre, artist, song)
        print(f'Storing song "{song}" by artist "{artist}" into the not_results.')
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
                f"Successfully stored data for song '{song}' by artist '{artist}' into the database spotify_data_songs."
            )
        except psycopg2.IntegrityError:
            conn.rollback()
            print(f"Duplicate entry detected: {genre}, {artist}, {song}. Skipping.")
    else:
        print(f"No matching artist-song combination found for {artist} - {song}")
        not_results(genre, artist, song)


def calculate_similarity(source: str, target: str) -> int:
    """Calculate the similarity score between two strings."""
    return fuzz.ratio(source, target)


def validate_result_structure(result: Dict[str, Any]) -> bool:
    """Check if the result structure is as expected."""
    return (
        isinstance(result, dict)
        and "artists" in result
        and isinstance(result["artists"], list)
        and result["artists"]
    )


def find_best_match(
    artist: str,
    song: str,
    album: Optional[str],
    results: List[Dict[str, Any]],
    artist_threshold: int = 25,
    song_threshold: int = 25,
    debug: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Find the best match for a song from a list of results based on artist, song, and optionally album.
    """
    best_match = None
    best_score = -1

    for idx, result in enumerate(results):
        if not validate_result_structure(result):
            if debug:
                print(f"DEBUG - Skipping result {idx} due to unexpected structure.")
            continue

        artist_similarity = calculate_similarity(artist, result["artists"][0]["name"])
        song_similarity = calculate_similarity(song, result["name"])

        if debug:
            print(f"DEBUG - Result {idx} artist similarity: {artist_similarity}")
            print(f"DEBUG - Result {idx} song similarity: {song_similarity}")

        if artist_similarity > artist_threshold and song_similarity > song_threshold:
            current_score = artist_similarity + song_similarity

            if album and "album" in result and result["album"].get("name") == album:
                current_score += 10
                if debug:
                    print(f"DEBUG - Result {idx} matched album, boosting score.")

            if debug:
                print(f"DEBUG - Result {idx} current score: {current_score}")

            if current_score > best_score:
                best_score = current_score
                best_match = result
        elif debug:
            print(f"DEBUG - Result {idx} discarded due to low similarity.")

    return best_match


def main():
    ensure_spotify_data_table_exists()
    try:
        token = get_token()
        if not token:
            print("Could not obtain token. Exiting...")
            return
        headers = get_auth_headers(token)
        get_unique_genre_music_list = get_unique_genre_music(cur)
        print(f"Unique genre music list: {len(get_unique_genre_music_list)}")
        for unique in get_unique_genre_music_list:
            genre = unique[0]
            artist = unique[1]
            album = unique[2]
            song = unique[3]
            print(f"Genre: {genre}, Artist: {artist}, Album: {album}, Song: {song}")
            try:
                search_and_store_spotify_data(genre, artist, song, headers, album)
            except Exception as e:
                print(f"An error occurred: {e}")
                print("Refreshing token...")
                token = get_token()
                if not token:
                    print("Could not obtain token. Exiting...")
                    return
                headers = get_auth_headers(token)

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
