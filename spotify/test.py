from SpotifyClass_file import SpotifyClass

spotify = SpotifyClass()
spotify.ensure_spotify_data_table_exists()
spotify.get_music_albums()
spotify.make_unique_music_albums()

result = spotify.search_album()
