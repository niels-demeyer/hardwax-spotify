from SpotifyClass_file import SpotifyClass

spotify = SpotifyClass()

table = spotify.get_playlist_tables()
print(table)

for x in table:
    results = spotify.select_playlist(x)
    print(f"Playlist: {x} - {len(results)} songs found.")
