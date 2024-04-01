"""

With this script, we can reset the 'not_found' column in the 'spotify_data_albums' table to 0. This is useful when we want to re-run the script that fetches the data from the Spotify API.

"""

from SpotifyClass_file import SpotifyClass

spotify = SpotifyClass()
id = spotify.select_id("spotify_data_albums")
spotify.reset_not_found(id)
