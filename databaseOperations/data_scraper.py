import sys
import os
import psycopg2
import json
import re

# Add the path to the config module to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# Establishing the database connection
try:
    connection = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )
    cursor = connection.cursor()
    print("Connected to database successfully")
except Exception as e:
    print(f"Error: {e}")
    sys.exit()


def process_and_insert_data(connection, cursor, genre_name):
    # Function to extract song titles from a given HTML content using the refined regex pattern
    def extract_song_titles_refined(html):
        matches = re.findall(
            r'<li class="rq".*?<span class="[^"]+"><span class="[^"]+"></span>\u2002([^<]+)</span>([^<]+)?',
            html,
        )
        return ["".join(match).strip() for match in matches]

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
        song_titles = extract_song_titles_refined(html)

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

    # Create the main table (if it doesn't already exist) and add columns for label_name and label_issue
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {genre_name}_music (
        id SERIAL PRIMARY KEY,
        artist VARCHAR(255),
        project_title VARCHAR(255),
        label_name VARCHAR(255),
        label_issue VARCHAR(255),
        artist_id VARCHAR(255),
        UNIQUE(artist, project_title, label_name, label_issue)
    );
    """
    try:
        cursor.execute(create_table_query)
        connection.commit()
    except Exception as e:
        print(f"Error: {e}")
        connection.rollback()

    # Create the {genre_name}_songs table
    create_songs_table_query = f"""
    CREATE TABLE IF NOT EXISTS {genre_name}_songs (
        id SERIAL PRIMARY KEY,
        {genre_name}_music_id INTEGER REFERENCES {genre_name}_music(id),
        song_title VARCHAR(255),
        UNIQUE({genre_name}_music_id, song_title)  -- Unique constraint to prevent duplicates
    );
    """
    try:
        cursor.execute(create_songs_table_query)
        connection.commit()
    except Exception as e:
        print(f"Error: {e}")
        connection.rollback()

    # Insert the extracted data into the {genre_name}_music table, and song titles into {genre_name}_songs table
    insert_ambient_query = f"""
    INSERT INTO {genre_name}_music (artist, project_title, label_name, label_issue) 
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (artist, project_title, label_name, label_issue) DO NOTHING
    RETURNING id
    """
    insert_song_query = f"""
    INSERT INTO {genre_name}_songs ({genre_name}_music_id, song_title) 
    VALUES (%s, %s)
    ON CONFLICT ({genre_name}_music_id, song_title) DO NOTHING  -- Skip duplicates
    """

    for record in extracted_data:
        try:
            cursor.execute(
                insert_ambient_query,
                (
                    record["artist"],
                    record["project_title"],
                    record["label_name"],
                    record["label_issue"],
                ),
            )
            music_id = cursor.fetchone()
            connection.commit()
        except Exception as e:
            print(f"Error: {e}")
            connection.rollback()

        if music_id:  # If a new entry was added to ambient_music
            for song in record["song_titles"]:
                try:
                    cursor.execute(insert_song_query, (music_id[0], song))
                    connection.commit()
                except Exception as e:
                    print(f"Error: {e}")
                    connection.rollback()

    print(
        f"Data and song titles for {genre_name} successfully inserted into the database!"
    )


# List of genres to process
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

for genre_name in genres:
    process_and_insert_data(connection, cursor, genre_name)
# Close the cursor and connection after all iterations have completed
cursor.close()
connection.close()
