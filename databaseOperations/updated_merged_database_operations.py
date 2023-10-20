import sys
import os
import psycopg2
import json
import re

# Add the path to the config module to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# Establishing the database connection
connection = psycopg2.connect(
    host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
)
cursor = connection.cursor()


def process_genre(genre_name):
    # Load the JSON content from the file
    directory_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "requests", "outputs", genre_name)
    )

    with open(f"{directory_path}/{genre_name}_all.json", "r") as file:
        json_content = json.load(file)

    # Extract the artist, project title, label name, label issue, and song titles from each entry
    extracted_data = []
    for entry in json_content:
        title = entry.get("result", {}).get("title", "")
        html = entry.get("result", {}).get("html", "")
        match_label = re.search(r'<a class title="([^"]+)" href="/label/', html)
        label_name = match_label.group(1) if match_label else ""
        end_pos = html.find("</a>", html.find('<a class title="'))
        start_pos = html.find(">", end_pos + 4) + 1
        end_next_pos = html.find("</a>", start_pos)
        label_issue = html[start_pos:end_next_pos] if end_pos != -1 else ""
        song_titles = re.findall(r'<span class="song_title">([^<]+)</span>', html)

        if title:
            artist, _, project_title = title.partition(":")
            extracted_data.append(
                {
                    "artist": artist.strip(),
                    "project_title": project_title.strip(),
                    "label_name": label_name,
                    "label_issue": label_issue,
                    "song_titles": song_titles,
                }
            )

    # Create the main genre table
    create_genre_music_table_query = f"""
    CREATE TABLE IF NOT EXISTS {genre_name}_music (
        id SERIAL PRIMARY KEY,
        artist VARCHAR(255),
        project_title VARCHAR(255),
        label_name VARCHAR(255),
        label_issue VARCHAR(255),
        artist_id VARCHAR(255),
        artist_check BOOLEAN DEFAULT FALSE,
        UNIQUE(artist, project_title, label_name, label_issue)
    );
    """
    cursor.execute(create_genre_music_table_query)

    # Create the genre songs table
    create_genre_songs_table_query = f"""
    CREATE TABLE IF NOT EXISTS {genre_name}_songs (
        id SERIAL PRIMARY KEY,
        {genre_name}_music_id INTEGER REFERENCES {genre_name}_music(id),
        song_title VARCHAR(255),
        UNIQUE({genre_name}_music_id, song_title)
    );
    """
    cursor.execute(create_genre_songs_table_query)

    # Insert the extracted data into the genre_music table, and song titles into genre_songs table
    insert_genre_query = f"""
    INSERT INTO {genre_name}_music (artist, project_title, label_name, label_issue) 
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (artist, project_title, label_name, label_issue) DO NOTHING
    RETURNING id
    """
    insert_song_query = f"""
    INSERT INTO {genre_name}_songs ({genre_name}_music_id, song_title) 
    VALUES (%s, %s)
    ON CONFLICT ({genre_name}_music_id, song_title) DO NOTHING
    """

    for record in extracted_data:
        cursor.execute(
            insert_genre_query,
            (
                record["artist"],
                record["project_title"],
                record["label_name"],
                record["label_issue"],
            ),
        )
        genre_music_id = cursor.fetchone()
        if genre_music_id:
            for song in record["song_titles"]:
                cursor.execute(insert_song_query, (genre_music_id[0], song))

    # Replace HTML entities in the genre_music and genre_songs tables
    update_music_query = f"""
    UPDATE {genre_name}_music
    SET 
        artist = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(artist, '&amp;', '&'), '&lt;', '<'), '&gt;', '>'), '&quot;', '"'), '&#39;', ''''),
        project_title = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(project_title, '&amp;', '&'), '&lt;', '<'), '&gt;', '>'), '&quot;', '"'), '&#39;', ''''),
        label_name = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(label_name, '&amp;', '&'), '&lt;', '<'), '&gt;', '>'), '&quot;', '"'), '&#39;', ''''),
        label_issue = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(label_issue, '&amp;', '&'), '&lt;', '<'), '&gt;', '>'), '&quot;', '"'), '&#39;', '''')
    """

    update_songs_query = f"""
    UPDATE {genre_name}_songs
    SET 
        song_title = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(song_title, '&amp;', '&'), '&lt;', '<'), '&gt;', '>'), '&quot;', '"'), '&#39;', '''')
    """

    cursor.execute(update_music_query)
    cursor.execute(update_songs_query)


# Calling the process_genre function for all genres
genres = [
    "ambient",
    "basicChannel",
    "chicago",
    "collectors",
    "colundi",
    "detroit",
    "detroit_house",
    "digital",
    "disco",
    "drexciya",
    "drum_n_bass",
    "electro",
    "essentials",
    "exclusives",
    "grime",
    "honestjons",
    "house",
    "irdial_discs",
    "last_week",
    "mego",
    "new_global_styles",
    "outernational",
    "reggae",
    "reissues",
    "surgeon",
    "techno",
    "this_week",
    "wave",
]
for genre in genres:
    process_genre(genre)

# Committing changes and closing the connection
connection.commit()
cursor.close()
connection.close()
