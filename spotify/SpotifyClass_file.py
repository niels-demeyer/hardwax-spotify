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
from psycopg2 import sql
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


class SpotifyClass:
    def __init__(self):
        load_dotenv()
        # load the environment variables for the database
        self.dbname = os.getenv("DB_NAME")
        self.dbuser = os.getenv("DB_USER")
        self.dbpassword = os.getenv("DB_PASSWORD")
        self.dbhost = os.getenv("DB_HOST")
        self.dbport = os.getenv("DB_PORT")
        self.conn = psycopg2.connect(
            dbname=self.dbname,
            user=self.dbuser,
            password=self.dbpassword,
            host=self.dbhost,
            port=self.dbport,
        )
        print("Database connected")

        # load the environment variables for the spotipy library
        self.spotipy_client_id = os.getenv("SPOTIPY_CLIENT2")
        self.spotipy_client_secret = os.getenv("SPOTIPY_SECRET2")
        # print(
        #     f"Client ID: {self.spotipy_client_id}, Secret: {self.spotipy_client_secret}"
        # )
        self.auth_manager = SpotifyClientCredentials(
            client_id=self.spotipy_client_id, client_secret=self.spotipy_client_secret
        )
        self.sp = spotipy.Spotify(auth_manager=self.auth_manager)

        # Define the variables
        self.spotify_data_songs = []
        self.music_albums_all = []
        self.music_albums_unique = []
        self.album_results = []

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
            print("Ensuring spotify_data_songs table exists...")
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
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
                    self.create_spotify_data_table()
        except Exception as e:
            print(f"Error in ensuring table exists: {e}")

    def create_spotify_data_table(self):
        try:
            print("Attempting to create spotify_data_songs table...")
            create_table_query = """
            CREATE TABLE IF NOT EXISTS spotify_data_songs (
                id SERIAL PRIMARY KEY,
                artist VARCHAR(255),
                label VARCHAR(255),
                label_issue VARCHAR(255),
                genre VARCHAR(255),
                track VARCHAR(255),
                album_uri VARCHAR(255),
                artist_uri VARCHAR(255),
                UNIQUE(id, artist, track)
            );
            """
            with self.conn.cursor() as cur:
                cur.execute(create_table_query)
            self.conn.commit()
            print("Table spotify_data_songs ensured to exist successfully")
        except Exception as e:
            print(f"Error in creating table: {e}")

    def get_spotify_data_songs(self):
        """
        Get the data from the songs table in the database.
        """
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM spotify_data_songs ORDER BY id DESC")
            self.spotify_data_songs = cur.fetchall()
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
            distinct_music_albums = cur.fetchall()
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
                        album[0],  # assuming id is at index 0
                        album[2],  # assuming artist is at index 2
                        album[3],  # assuming album is at index 3
                    ),
                )
            self.conn.commit()
        except Exception as e:
            print(f"Error in updating music albums: {e}")

    def search_album(self) -> Dict[str, Any]:
        """
        Search for an album on Spotify by its name and artist, and return all its tracks.
        """
        for music_album in self.music_albums_unique:
            album = music_album["album"]
            artist = music_album["artist"]
            while True:
                try:
                    results = self.sp.search(
                        q=f"album:{album} artist:{artist}", type="album"
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
                        # self.save_to_database()
                        self.save_to_json()
                    else:
                        self.album_results.append(music_album)
                        print(f"Album not found: {album} by {artist}")
                        # self.save_to_database()
                        self.save_to_json()
                    break
                except spotipy.exceptions.SpotifyException as e:
                    if e.http_status == 429:
                        print("Rate limit exceeded. Waiting...")
                        time.sleep(int(e.headers["Retry-After"]))
                        continue
                    else:
                        print(f"Error occurred while searching for album: {e}")
                        break

    def save_to_json(self):
        """
        Save the album results to a JSON file.
        """
        try:
            with open("album_results.json", "w") as f:
                json.dump(self.album_results, f, indent=4)
        except Exception as e:
            print(f"Error in saving to JSON: {e}")

    def save_to_database(self):
        """
        Save the album results to the database.
        """
        try:
            with self.conn.cursor() as cur:
                for album in self.album_results:
                    artist_uri = album.get("artist_uri", None)
                    album_uri = album.get("album_uri", None)
                    cur.execute(
                        sql.SQL(
                            """
                            INSERT INTO spotify_data_songs (artist, label, label_issue, genre, track, album_uri, artist_uri)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO NOTHING;
                            """
                        ),
                        (
                            album["artist"],
                            album["label"],
                            album["label_issue"],
                            album["genre"],
                            album["track"],
                            album_uri,
                            artist_uri,
                        ),
                    )
                self.conn.commit()
        except Exception as e:
            print(f"Error in saving to database: {e}")
