# hardwax-spotify
This project aims to scrape all the music data from [Hardwax](https://hardwax.com) and create genre-based playlists on Spotify.

# results
The results can be found using the following link 
| playlist             | Link                                                       |
|-------------------|------------------------------------------------------------|
| Playlist for Ambient| [Listen on Spotify](https://open.spotify.com/playlist/1YIbBAiJbS2FwFOFNOY1M9?si=4db7022f993c4e97) |
| Playlist for exclusives| [Listen on Spotify](https://open.spotify.com/playlist/3QTCit285mo6LMJDdEcpql?si=69831571da834c46) |
| Playlist for essentials | [Listen on Spotify](https://open.spotify.com/playlist/297JjaNBOxKABsLem3lDxq?si=27f6e5468991437f) |

## Configuration Setup

### 1. Database Configuration
Create a `config.py` file in your project root directory and configure the database connection parameters:

```python
# Database configuration
DB_HOST = 'your_postgresql_host'
DB_PORT = 'your_postgresql_port'
DB_NAME = 'your_database_name'
DB_USER = 'your_database_user'
DB_PASSWORD = 'your_database_password'
```

### 2. Spotify Configuration
In the same `config.py` file, set up the Spotify configuration parameters:

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

## requests
In the requests folder you will find a script for each genre. The script requests data from the hardwax api and outputs it in a json object. 

### HTTP Headers Configuration
Each script requires specific HTTP headers to perform web requests successfully. You need to define these headers at the beginning of each script. Use a tool like Insomnia to capture the necessary headers from your web interactions. Here is an example of how to set up the headers:

```python
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "authority": "example.com",
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    "cookie": "sessionid=YOUR_SECURE_SESSION_ID; other_cookie=ANOTHER_SECURE_COOKIE",
    "dnt": "1",
    "if-none-match": "A_UNIQUE_CACHE_IDENTIFIER",
    "referer": "https://hardwax.com/basic-channel/?page=1",
    "sec-ch-ua": "Browser_Version_Information",
}

```
### run requests
To run all the requests at once, just run the run_requests.py file in the root of the project.
Next run the run_databaseOperations.py file to get all the json info into a your postgresql database.

# spotify api
The last thing to do is to run th two files in the spotify folder.
| file             | result                                                       |
|-------------------|------------------------------------------------------------|
| search_songs.py | Takes all the information from the genre_music, genre_songs tables and looks for matches on spotify. All the results are stored into the spotify_data_songs table. |
| add_to_playlists.py | Makes genre specific playlists with all the data from the spotify_data_songs table. |
