import os
from dotenv import load_dotenv
import pprint
import psycopg2
from psycopg2.extras import DictCursor
import base64
import json
from requests import post, get
import time
from fuzzywuzzy import fuzz
from typing import List, Optional, Dict, Any
from requests import post, get, put
from datetime import datetime
from psycopg2 import sql, OperationalError
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import re
from datetime import datetime
import csv


class SpotifyClass:
    def __init__(self):
        load_dotenv()
        # load the environment variables for the database
        self.dbname = os.getenv("DB_NAME")
        self.dbuser = os.getenv("DB_USER")
        self.dbpassword = os.getenv("DB_PASSWORD")
        self.dbhost = os.getenv("DB_HOST")
        self.dbport = os.getenv("DB_PORT")
        try:
            self.conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.dbuser,
                password=self.dbpassword,
                host=self.dbhost,
                port=self.dbport,
            )
            cur = self.conn.cursor()  # Create a cursor object
            cur.execute("SELECT 1")  # Execute a simple query
            print("Database connected")
        except OperationalError as e:
            print(f"The error '{e}' occurred")

        # load the environment variables for the spotipy library
        self.spotipy_client_id = os.getenv("SPOTIPY_CLIENT3")
        self.spotipy_client_secret = os.getenv("SPOTIPY_SECRET3")
        self.spotipy_redirect_uri = "https://localhost:8085"
        self.auth_manager = SpotifyOAuth(
            client_id=self.spotipy_client_id,
            client_secret=self.spotipy_client_secret,
            redirect_uri=self.spotipy_redirect_uri,
            scope="playlist-modify-public",  # add the playlist-modify-public scope
        )
        self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
        # Start the authorization process
        self.sp.me()
        # Define the variables
        self.spotify_data_albums = []
        self.music_albums_all = []
        self.music_albums_unique = None
        self.album_results = []

    def print_all_databases(self):
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT datname FROM pg_database;")
            rows = cur.fetchall()

            for row in rows:
                print("Database name: ", row[0])
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if cur is not None:
                cur.close()

    def search_artist(self, artist_name: str) -> Dict[str, Any]:
        """
        Search for an artist on Spotify.
        """
        try:
            result = self.sp.search(q=artist_name, type="artist")
            return result
        except Exception as e:
            print(f"Error in searching artist: {e}")

    def damerau_levenshtein_distance(self, s1, s2):
        """
        Calculate the Damerau–Levenshtein distance between two strings.
        """
        len_s1 = len(s1)
        len_s2 = len(s2)
        d = [[0] * (len_s2 + 1) for _ in range(len_s1 + 1)]

        for i in range(len_s1 + 1):
            d[i][0] = i
        for j in range(len_s2 + 1):
            d[0][j] = j

        for i in range(1, len_s1 + 1):
            for j in range(1, len_s2 + 1):
                cost = 0 if s1[i - 1] == s2[j - 1] else 1
                d[i][j] = min(
                    d[i - 1][j] + 1,  # deletion
                    d[i][j - 1] + 1,  # insertion
                    d[i - 1][j - 1] + cost,  # substitution
                )
                if (
                    i > 1
                    and j > 1
                    and s1[i - 1] == s2[j - 2]
                    and s1[i - 2] == s2[j - 1]
                ):
                    d[i][j] = min(d[i][j], d[i - 2][j - 2] + cost)  # transposition

        return d[len_s1][len_s2]

    def are_strings_similar(self, s1, s2, threshold):
        """
        Compare if two strings are similar based on a threshold.
        """
        distance = self.damerau_levenshtein_distance(s1, s2)
        if distance <= threshold:
            return True
        else:
            return False

    def ensure_spotify_data_table_exists(self):
        try:
            print("Ensuring spotify_data_albums table exists...")
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'spotify_data_albums'
                    );
                    """
                )
                result = cur.fetchone()
                if result[0]:
                    print("Table spotify_data_albums exists")
                    return True
                else:
                    self.create_spotify_data_table_album()
        except Exception as e:
            print(f"Error in ensuring table exists: {e}")

    def create_spotify_data_table_album(self):
        try:
            print("Attempting to create spotify_data_albums table...")
            create_table_query = """
            CREATE TABLE IF NOT EXISTS spotify_data_albums (
                id SERIAL PRIMARY KEY,
                checked BOOLEAN DEFAULT FALSE,
                artist VARCHAR(255),
                album VARCHAR(255),
                album_uri VARCHAR(255),
                artist_uri VARCHAR(255),
                UNIQUE(id, artist, album)
            );
            """
            with self.conn.cursor() as cur:
                cur.execute(create_table_query)
            self.conn.commit()
            print("Table spotify_data_albums ensured to exist successfully")
        except Exception as e:
            print(f"Error in creating table: {e}")

    def get_spotify_data_albums(self):
        """
        Get the data from the songs table in the database.
        """
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM spotify_data_albums ORDER BY id DESC")
            self.spotify_data_albums = cur.fetchall()
        except Exception as e:
            print(f"Error in getting spotify data songs: {e}")

    def get_music_albums(self):
        """
        Get the data from the albums table in the database.
        """
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM music_albums")
            colnames = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            for row in rows:
                self.music_albums_all.append(dict(zip(colnames, row)))
            return self.music_albums_all
        except Exception as e:
            print(f"Error in getting music albums: {e}")

    def make_unique_music_albums_table(self):
        """
        Update the unique music albums table.
        """
        try:
            cur = self.conn.cursor()
            cur.execute(
                """
                SELECT DISTINCT ON (artist, album) * FROM music_albums
                """
            )
            column = [description[0] for description in cur.description]
            distinct_music_albums = [dict(zip(column, row)) for row in cur.fetchall()]
            cur.execute(
                """CREATE TABLE IF NOT EXISTS music_albums_unique( 
                id INT PRIMARY KEY,
                checked BOOLEAN DEFAULT FALSE,
                artist VARCHAR(255),
                album VARCHAR(255),
                UNIQUE(artist, album)
                )
                """
            )
            self.conn.commit()
            for album in distinct_music_albums:
                cur.execute(
                    """
                    INSERT INTO music_albums_unique (id, artist, album) VALUES (%s, %s, %s)
                    ON CONFLICT (artist, album) DO NOTHING
                    """,
                    (
                        album["id"],
                        album["artist"],
                        album["album"],
                    ),
                )
            self.conn.commit()
        except Exception as e:
            print(f"Error in updating music albums: {e}")

    def get_unique_music_albums(self):
        """
        Fetch from the music_albums_unique table and return as a dict
        """
        try:
            self.make_unique_music_albums_table()
            cur = self.conn.cursor()
            cur.execute(
                """
            SELECT * from music_albums_unique WHERE checked = False
            """
            )
            column = [description[0] for description in cur.description]
            self.music_albums_unique = [
                dict(zip(column, row)) for row in cur.fetchall()
            ]
        except Exception as e:
            print("Error in get_unique_music_albums:", e)

    def search_album(self) -> Dict[str, Any]:
        """
        Search for an album on Spotify by its name and artist, and returns the artist_uri and album_uri
        """
        for music_album in self.music_albums_unique:
            album = music_album["album"]
            artist = music_album["artist"]
            album_id = music_album["id"]  # assuming your dictionary includes the id
            not_found = []
            while True:
                try:
                    results = self.sp.search(
                        q=f"album:{album} artist:{artist}", type="album", market="BE"
                    )
                    print(f"Searching for album: {album} by {artist}")
                    if results["albums"]["items"]:
                        album_uri = results["albums"]["items"][0]["uri"]
                        artist_uri = results["albums"]["items"][0]["artists"][0]["uri"]
                        music_album_with_uri = {
                            **music_album,
                            "album_uri": album_uri,
                            "artist_uri": artist_uri,
                        }
                        self.album_results.append(music_album_with_uri)
                        print(f"Album found: {album} by {artist}")
                        self.save_to_database_album()
                        # self.save_to_json()
                    else:
                        not_found.append((album, artist))  # append as a tuple
                        print(f"Album not found: {album} by {artist}")
                        self.save_to_csv(input_data=not_found)
                    self.update_checked_status("music_albums_unique", album_id)
                    break
                except spotipy.exceptions.SpotifyException as e:
                    if e.http_status == 429:
                        print("Rate limit exceeded. Waiting...")
                        time.sleep(int(e.headers["Retry-After"]))
                        continue
                    else:
                        print(f"Error occurred while searching for album: {e}")

    def search_track(self, spotify_data_albums):
        """
        Search for all the tracks in the albums that we have
        """
        errors = []  # List to store any errors that occur
        for i, album in enumerate(spotify_data_albums):
            # Stop after 50 albums
            if i >= 2000:
                break

            album_uri = album["album_uri"]
            artist_uri = album["artist_uri"]

            # Extract the IDs from the URIs
            album_id_match = re.search(r"spotify:album:(\w+)", album_uri)
            artist_id_match = re.search(r"spotify:artist:(\w+)", artist_uri)

            if album_id_match and artist_id_match:
                album_id = album_id_match.group(1)

                try:
                    # Get the tracks of the album
                    tracks = self.get_album_tracks(album_id)
                    print(f"Searching for tracks in album {album_id}")

                    # Add the tracks to the album dictionary
                    album["searched_tracks"] = tracks

                    # Update the checked status
                    self.update_checked_status("spotify_data_albums", album["id"])
                except Exception as e:
                    # If an error occurs, add it to the errors list
                    errors.append(str(e))

        return spotify_data_albums, errors

    def get_album_tracks(self, album_id):
        """
        Get the tracks of an album
        """
        try:
            # Get the album's tracks
            results = self.sp.album_tracks(album_id)

            # Extract the track name and ID from each track
            tracks = [
                {"name": track["name"], "id": track["id"]} for track in results["items"]
            ]

            return tracks
        except Exception as e:
            print(f"Error occurred while getting tracks for album {album_id}: {e}")

    def make_spotify_data_songs_table(self):
        """
        Makes the spotify_data_songs table
        """
        try:
            cur = self.conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS spotify_data_songs (
                    id VARCHAR(255),
                    track VARCHAR(255),
                    track_id VARCHAR(255) UNIQUE,
                    artist VARCHAR(255),
                    album VARCHAR(255),
                    album_uri VARCHAR(255),
                    artist_uri VARCHAR(255),
                    genre VARCHAR(255),
                    UNIQUE(track, track_id)
                )
                """
            )
            self.conn.commit()
        except Exception as e:
            print(f"Error in making spotify_data_songs table: {e}")

    def save_to_spotify_data_songs(self, spotify_data_albums):
        """
        Save the track results to the database.
        """
        try:
            with self.conn.cursor() as cur:
                self.make_spotify_data_songs_table()
                for album in spotify_data_albums:
                    if "searched_tracks" in album:
                        artist = album.get("artist", None)
                        album_name = album.get("album", None)
                        artist_uri = album.get("artist_uri", None)
                        album_uri = album.get("album_uri", None)
                        id = album.get("id", None)
                        for track in album["searched_tracks"]:
                            track_name = track.get("name", None)
                            track_id = track.get("id", None)

                            cur.execute(
                                sql.SQL(
                                    """
                                    INSERT INTO spotify_data_songs (id, track, track_id, artist, album, album_uri, artist_uri)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                                    ON CONFLICT (track_id) DO NOTHING;
                                    """
                                ),
                                (
                                    id,
                                    track_name,
                                    track_id,
                                    artist,
                                    album_name,
                                    album_uri,
                                    artist_uri,
                                ),
                            )
                self.conn.commit()
        except Exception as e:
            print(f"Error in saving to database: {e}")

    def select_id(self, table_name):
        """
        Gets the ID of all the rows in a table
        """
        cur = self.conn.cursor()
        cur.execute(f"SELECT * FROM {table_name}")
        rows = cur.fetchall()
        # Extract the first element of each tuple and add it to a set
        ids = [row[0] for row in rows]
        return ids

    def reset_not_found(self, album_ids):
        """
        Resets the album in music_albums_unique to False for albums that are not found
        """
        try:
            cur = self.conn.cursor()
            # Convert the list of IDs to a string of comma-separated values
            ids_str = ",".join(map(str, album_ids))
            cur.execute(
                f"""
                UPDATE music_albums_unique SET checked = False WHERE id NOT IN ({ids_str})
                """
            )
            self.conn.commit()
        except Exception as e:
            print("Error in reset_not_found:", e)

    def update_checked_status(self, table, album_id):
        """
        Update the checked status of an album in the music_albums_unique table
        """
        try:
            cur = self.conn.cursor()
            cur.execute(
                f"""
                UPDATE {table} SET checked = True WHERE id = %s
                """,
                (album_id,),
            )
            self.conn.commit()
        except Exception as e:
            print("Error in update_checked_status:", e)

    def save_to_csv(self, input_data: List[tuple[str, str]]):
        """
        Save the album results to a CSV file by appending new data.
        """
        try:
            # Convert tuples to dictionaries
            dict_data = [
                {"album": album, "artist": artist} for album, artist in input_data
            ]

            # Append to the existing file or create a new one
            with open("album_results.csv", "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["album", "artist"])
                if f.tell() == 0:
                    writer.writeheader()
                writer.writerows(dict_data)
        except Exception as e:
            print(f"Error in saving to CSV: {e}")

    def save_to_database_album(self):
        """
        Save the album results to the database.
        """
        try:
            with self.conn.cursor() as cur:
                for album in self.album_results:
                    if "artist_uri" in album and "album_uri" in album:
                        id = album.get("id", None)
                        artist = album.get("artist", None)
                        album_name = album.get("album", None)
                        artist_uri = album["artist_uri"]
                        album_uri = album["album_uri"]

                        cur.execute(
                            sql.SQL(
                                """
                                INSERT INTO spotify_data_albums (id, artist, album, album_uri, artist_uri)
                                VALUES (%s, %s, %s, %s, %s)
                                ON CONFLICT (id) DO NOTHING;
                                """
                            ),
                            (
                                id,
                                artist,
                                album_name,
                                album_uri,
                                artist_uri,
                            ),
                        )
                self.conn.commit()
        except Exception as e:
            print(f"Error in saving to database: {e}")

    def select_table_dict(self, table_name):
        """
        Select the whole table and return it as a dictionary
        """
        try:
            cur = self.conn.cursor()
            cur.execute(f"SELECT * FROM {table_name} WHERE checked = False")
            column = [description[0] for description in cur.description]
            result = [dict(zip(column, row)) for row in cur.fetchall()]
            return result
        except Exception as e:
            print(f"Error in select_table_dict: {e}")

    def add_genre_playlist(self):
        """
        Add the genre of spotify_data_song to each item and add it to the spotify_data_songs table.
        """
        cursor = self.conn.cursor()

        try:
            # Update the genre of songs in one SQL query
            cursor.execute(
                """
                UPDATE spotify_data_songs
                SET genre = music_albums.genre
                FROM music_albums
                WHERE spotify_data_songs.id::text = music_albums.id::text
                """
            )
        except psycopg2.errors.UniqueViolation:
            self.conn.rollback()
            cursor.execute(
                """
                DELETE FROM spotify_data_songs
                WHERE id IN (
                    SELECT spotify_data_songs.id
                    FROM spotify_data_songs
                    JOIN music_albums ON spotify_data_songs.id::text = music_albums.id::text
                    WHERE spotify_data_songs.genre = music_albums.genre
                )
                """
            )
            cursor.execute(
                """
                UPDATE spotify_data_songs
                SET genre = music_albums.genre
                FROM music_albums
                WHERE spotify_data_songs.id::text = music_albums.id::text
                """
            )

        self.conn.commit()

    def get_songs_split_by_genre(self):
        """
        Fetch all rows from the spotify_data_songs table, order them by id,
        split them by genre, and create a new table for each genre.
        """
        cursor = self.conn.cursor()

        # Fetch all rows from the spotify_data_songs table and order them by id
        cursor.execute("SELECT * FROM spotify_data_songs ORDER BY id")
        songs = cursor.fetchall()

        # Convert the rows to dictionaries
        columns = [desc[0] for desc in cursor.description]
        songs = [dict(zip(columns, song)) for song in songs]

        # Split the songs by genre
        songs_by_genre = {}
        genre_counts = {}
        for song in songs:
            genre = song["genre"]
            if genre not in songs_by_genre:
                songs_by_genre[genre] = []
                genre_counts[genre] = 1
            else:
                genre_counts[genre] += 1

            # If the number of songs for a genre exceeds 10000, create a new genre category
            if genre_counts[genre] > 10000:
                count = genre_counts[genre] // 10000
                new_genre = f"{genre}_{count}"
                if new_genre not in songs_by_genre:
                    songs_by_genre[new_genre] = []
                songs_by_genre[new_genre].append(song)
                genre_counts[new_genre] = len(songs_by_genre[new_genre])
            else:
                songs_by_genre[genre].append(song)

        # Create a new table for each genre
        for genre, songs in songs_by_genre.items():
            table_name = genre.replace(
                " ", "_"
            )  # Replace spaces with underscores to create a valid SQL table name

            # Check if the table already exists
            cursor.execute(f"SELECT to_regclass('{table_name}')")
            if not cursor.fetchone()[0]:
                # If the table does not exist, create it
                cursor.execute(
                    f'CREATE TABLE "{table_name}" AS SELECT * FROM spotify_data_songs WHERE genre = %s',
                    (genre,),
                )

            # Insert the songs into the table, avoiding duplicate entries
            values = [
                tuple(str(song[column])[:255] for column in columns) for song in songs
            ]  # Truncate the string to 255 characters
            insert_sql = f'INSERT INTO "{table_name}" VALUES ({", ".join(["%s"] * len(values[0]))}) ON CONFLICT DO NOTHING'
            cursor.executemany(insert_sql, values)

        self.conn.commit()  # Commit the changes to the database

    def get_playlist_tables(self):
        """
        Get the names of the tables that store the playlists
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_catalog = 'scrapy_hardwax'
            AND table_schema = 'public'
            AND table_name != 'spotify_data_songs' 
            AND table_name != 'spotify_data_albums' 
            AND table_name != 'music_albums'
            AND table_name != 'music_albums_unique'
            AND table_name != 'labels'
            """
        )
        tables = cursor.fetchall()
        return [table[0] for table in tables]

    def select_playlist(self, table_name):
        """
        Select all the rows from a playlist table
        """
        cursor = self.conn.cursor()
        cursor.execute(f'SELECT * FROM "{table_name}"')
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]

    def create_and_populate_playlist(self, table_name, track_ids):
        """
        Create a playlist with the given table name and add tracks to it.
        """
        # Create a new playlist
        playlist_name = "hardwax_" + table_name
        playlist = self.sp.user_playlist_create(self.sp.me()["id"], playlist_name)
        print(f"Created playlist with ID: {playlist['id']}")  # print the playlist ID

        # Validate track_ids and convert them to URIs
        valid_track_uris = [
            f"spotify:track:{track_id}"
            for track_id in track_ids
            if re.match("^[a-zA-Z0-9]+$", track_id)
        ]

        # Add tracks to the new playlist

        if valid_track_uris:  # only proceed if there are valid track URIs
            # Split the list of URIs into chunks of 100 tracks
            for i in range(0, len(valid_track_uris), 100):
                chunk = valid_track_uris[i : i + 100]
                self.sp.playlist_add_items(playlist["id"], chunk)

        # Update the playlist description with the current date
        description = f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} check out hardwax.com for more!"
        self.sp.playlist_change_details(playlist["id"], description=description)

        return playlist
