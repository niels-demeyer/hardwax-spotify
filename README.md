# hardwax-spotify
This project aims to scrape all the music data from [Hardwax](https://hardwax.com) and create genre-based playlists on Spotify.

# results
The results can be found using the following link [Listen on Spotify](https://open.spotify.com/user/ur5o8bnri7ytv1sigoq2rkgt2/playlists)

## Configuration Setup

### 1. Database Configuration
Create a `.env` file in your project root directory and configure the database connection parameters:

```python
# Database configuration
DB_HOST = 'your_postgresql_host'
DB_PORT = 'your_postgresql_port'
DB_NAME = 'your_database_name'
DB_USER = 'your_database_user'
DB_PASSWORD = 'your_database_password'
```

### 2. Spotify Configuration
In the same `.env` file, set up the Spotify configuration parameters:

```python
# Spotify configuration
SPOTIFY_REDIRECT_URI = 'https://localhost:300'  # or your preferred redirect URI
SPOTIFY_USERNAME = 'your_spotify_user_id'
CLIENT_ID = 'your_spotify_client_id'  # obtain this from the Spotify Developer Dashboard
CLIENT_SECRET = 'your_spotify_client_secret'  # obtain this from the Spotify Developer Dashboard
REFRESH_TOKEN = 'your_spotify_refresh_token'  # obtain this by running refresh_token.py
```

### scrapy 
In the hardwax folder you can find a scrapy project that will scrape all the data for you. Simply run all the `run_all_spiders`.

# spotify api
The last thing to do is to run the files in the spotify folder.
| file             | result                                                       |
|-------------------|------------------------------------------------------------|
| search_albums.py | Takes the scraping data and searches for the artist-album combination and returns the spotify id. |
| search_songs | Gets all the tracks from the album and returns the spotify id.|
| make_playlist_tables.py | Splits the tracks into different tables based on how big the playlist can be on spotify |
| playlist.py | Makes the playlist tables into spotify playlists. |
