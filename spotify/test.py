from SpotifyClass_file import SpotifyClass

spotify = SpotifyClass()
is_similar = spotify.are_strings_similar("hello", "helo", 1)
print(is_similar)
