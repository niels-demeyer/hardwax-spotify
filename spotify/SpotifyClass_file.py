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
        # load the environment variables for the spotify api
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.refresh_token = os.getenv("REFRESH_TOKEN")
        self.spotify_username = os.getenv("SPOTIFY_USERNAME")
