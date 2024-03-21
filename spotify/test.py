from SpotifyClass_file import SpotifyClass

spotify = SpotifyClass()
spotify.ensure_spotify_data_table_exists()
result = spotify.search_album("Magda", "Donato Dozzy")
print(result)
