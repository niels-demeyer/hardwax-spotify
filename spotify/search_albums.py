"""

With this script, we can search for albums in the Spotify API. We can search for albums by name, artist. The search results are stored in the 'spotify_data_albums' table.

"""

from SpotifyClass_file import SpotifyClass

spotify = SpotifyClass()
spotify.ensure_spotify_data_table_exists()
spotify.get_unique_music_albums()
spotify.search_album()
