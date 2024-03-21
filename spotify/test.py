from SpotifyClass_file import SpotifyClass

spotify = SpotifyClass()
spotify.ensure_spotify_data_table_exists()
# spotify_data_songs = spotify.get_spotify_data_songs()

# print(spotify_data_songs)
spotify.get_music_albums()
spotify.make_unique_music_albums()
print(spotify.music_albums_unique)

spotify.search_spotify()
