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

### 3. Generating the Spotify Refresh Token
The `refresh_token.py` file is a script to help you generate a Spotify refresh token. To use it, follow these steps:

1. Replace the placeholders in `refresh_token.py` with your actual Spotify application values:

   ```python
   CLIENT_ID = 'your_spotify_client_id'
   CLIENT_SECRET = 'your_spotify_client_secret'
   REDIRECT_URI = 'http://localhost:8090/callback'  # or your preferred redirect URI
   ```

2. Run the `refresh_token.py` script. This will open a web browser, asking you to log in to Spotify and authorize your application.

3. After authorizing, you will be redirected to a local server, and the script will print the refresh token to the console. Copy this token and paste it in the `REFRESH_TOKEN` field in your `config.py` file.

### scrapy 
In the hardwax folder you can find a scrapy project that will scrape all the data for you. Simply run all the spiders.

#### command for powershell 
```
foreach ($spider in (scrapy list)) { scrapy crawl $spider }
```
#### command for bash
```
for spider in $(scrapy list); do scrapy crawl $spider; done
```

# spotify api
The last thing to do is to run the files in the spotify folder.
| file             | result                                                       |
|-------------------|------------------------------------------------------------|
| search_songs.py | Takes all the information from the genre_music, genre_songs tables and looks for matches on spotify. All the results are stored into the spotify_data_songs table. |
| playlist.py | Makes genre specific playlists with all the data from the spotify_data_songs table. The tables are stored in a seperate database called hardwax_spotify. The playlist_ids table consists of every id for each playlist.|
| api.py | Gets all the information from the hardwax_spotify database and communicates this using the spotify api.
