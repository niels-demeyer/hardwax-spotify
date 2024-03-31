from SpotifyClass_file import SpotifyClass

spotify = SpotifyClass()
id = spotify.select_id("spotify_data_albums")
spotify.reset_not_found(id)
