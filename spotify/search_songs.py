from SpotifyClass_file import SpotifyClass

spotify = SpotifyClass()

spotify_data_albums = spotify.select_table_dict("spotify_data_albums")
spotify.search_track(spotify_data_albums=spotify_data_albums)
