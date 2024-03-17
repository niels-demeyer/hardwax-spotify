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
