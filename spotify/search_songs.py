"""

With this script, we can search for songs in the Spotify API. We can search for songs by name, artist by using the spotify ID that we got from running the search_albums script. The search results are stored in the 'spotify_data_songs' table.

"""

from SpotifyClass_file import SpotifyClass

spotify = SpotifyClass()

spotify_data_albums = spotify.select_table_dict("spotify_data_albums")
if len(spotify_data_albums) == 0:
    print("No albums found in the database that still need to be searched.")
    exit()
result = spotify.search_track(spotify_data_albums=spotify_data_albums)
spotify.save_to_spotify_data_songs(result)
