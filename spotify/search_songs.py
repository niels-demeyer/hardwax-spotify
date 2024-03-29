from SpotifyClass_file import SpotifyClass

spotify = SpotifyClass()

spotify_data_albums = spotify.select_table_dict("spotify_data_albums")
if len(spotify_data_albums) == 0:
    print("No albums found in the database that still need to be searched.")
    exit()
result = spotify.search_track(spotify_data_albums=spotify_data_albums)
spotify.save_to_spotify_data_songs(result)
