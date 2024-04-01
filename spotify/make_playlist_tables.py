"""

With this script, we can create a table that contains the songs that are in the Spotify API. We can split the songs by genre and store them in the 'genre_suffix' table.

"""

from SpotifyClass_file import SpotifyClass

spotify = SpotifyClass()
spotify.add_genre_playlist()
spotify.get_songs_split_by_genre()
