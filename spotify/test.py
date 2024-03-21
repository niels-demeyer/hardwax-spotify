from SpotifyClass_file import SpotifyClass

spotify = SpotifyClass()
spotify.ensure_spotify_data_table_exists()
spotify.get_music_albums()
spotify.make_unique_music_albums()
# print(spotify.music_albums_all)
print(spotify.music_albums_unique)
