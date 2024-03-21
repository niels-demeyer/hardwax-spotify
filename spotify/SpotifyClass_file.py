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
        # load the environment variables for the spotify api
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.refresh_token = os.getenv("REFRESH_TOKEN")
        self.spotify_username = os.getenv("SPOTIFY_USERNAME")
        # api varialbes
        self.token = self.get_access_token()
        print("Spotify token acquired")
        self.headers = self.get_headers()
        print("Spotify headers acquired")

        # Define the variables
        self.spotify_data_songs = None
        self.music_albums = None

    # Functions to get the access token
    def get_access_token(self):
        try:
            print("Attempting to get Spotify token...")

            auth_string = self.client_id + ":" + self.client_secret
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

    # Function to get the headers
    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

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
            cur.execute("SELECT * FROM spotify_data_songs")
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
            self.music_albums = [dict(zip(colnames, row)) for row in rows]
            return self.music_albums
        except Exception as e:
            print(f"Error in getting music albums: {e}")
