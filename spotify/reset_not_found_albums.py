from SpotifyClass_file import SpotifyClass

spotify = SpotifyClass()
id = spotify.select_id("spotify_data_albums")
for x in id:
    spotify.update_checked_status(x)
