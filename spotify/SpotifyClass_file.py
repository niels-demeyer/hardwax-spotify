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
