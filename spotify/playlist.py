"""

With this script we can create a playlist in Spotify for each table in the database. 
We can create a playlist for each genre and populate it with the songs that are in the 'genre_suffix' table. The playlist will be named after the genre.
After the playlist is changed the descritpion will be updated with the date in the playlist.
It is important to note that the Spotify API has a limit of 11000 songs per playlist.
"""

from SpotifyClass_file import SpotifyClass

spotify = SpotifyClass()  # make sure to pass your Spotify credentials if needed

table = spotify.get_playlist_tables()
print(table)

for x in table:
    results = spotify.select_playlist(x)
    print(f"Playlist: {x} - {len(results)} songs found.")
    print(results[0].keys())

    # Assuming 'id' is the key for the track ID in each dictionary in results
    track_ids = [
        result.get("track_id") for result in results if result.get("id") is not None
    ]
    # Create and populate a Spotify playlist for each table
    spotify.create_and_populate_playlist(x, track_ids)

print("Done.")
