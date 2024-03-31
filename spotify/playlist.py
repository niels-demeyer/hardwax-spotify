from SpotifyClass_file import SpotifyClass

spotify = SpotifyClass()  # make sure to pass your Spotify credentials if needed

table = spotify.get_playlist_tables()
print(table)

for x in table:
    results = spotify.select_playlist(x)
    print(f"Playlist: {x} - {len(results)} songs found.")
    print(results[0].keys())

    # Assuming 'id' is the key for the track ID in each dictionary in results
    track_ids = [result["id"] for result in results]

    # Create and populate a Spotify playlist for each table
    spotify.create_and_populate_playlist(x, track_ids)

print("Done.")
