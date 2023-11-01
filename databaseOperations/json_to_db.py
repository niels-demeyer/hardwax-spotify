import sys
import os
import psycopg2
import json
import re
import html

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


def create_tables(cursor, genre_name):
    create_genre_music_table_query = f"""
    CREATE TABLE IF NOT EXISTS {genre_name}_music (
        id SERIAL PRIMARY KEY,
        artist VARCHAR(255),
        project_title VARCHAR(255),
        label_name VARCHAR(255),
        label_issue VARCHAR(255),
        UNIQUE(artist, project_title, label_name, label_issue)
    );
    """
    cursor.execute(create_genre_music_table_query)

    create_genre_songs_table_query = f"""
    CREATE TABLE IF NOT EXISTS {genre_name}_songs (
        id SERIAL PRIMARY KEY,
        {genre_name}_music_id INTEGER REFERENCES {genre_name}_music(id) ON DELETE CASCADE,
        song_title VARCHAR(255),
        UNIQUE({genre_name}_music_id, song_title)
    );
    """
    cursor.execute(create_genre_songs_table_query)


def extract_song_titles_refined(html_content):
    matches = re.findall(
        r'<li class="rq".*?<span class="[^"]+"><span class="[^"]+"></span>\u2002([^<]+)</span>([^<]+)?',
        html_content,
    )
    decoded_matches = [html.unescape("".join(match).strip()) for match in matches]
    return decoded_matches


def insert_data(cursor, genre_name, record):
    cursor.execute(
        f"""
        INSERT INTO {genre_name}_music (artist, project_title, label_name, label_issue)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (artist, project_title, label_name, label_issue)
        DO UPDATE SET
            artist = EXCLUDED.artist,
            project_title = EXCLUDED.project_title,
            label_name = EXCLUDED.label_name,
            label_issue = EXCLUDED.label_issue
        RETURNING id
        """,
        (
            record["artist"],
            record["project_title"],
            record["label_name"],
            record["label_issue"],
        ),
    )

    music_id = cursor.fetchone()
    if music_id:
        music_id = music_id[0]
        for song_title in record["song_titles"]:
            cursor.execute(
                f"""
                INSERT INTO {genre_name}_songs ({genre_name}_music_id, song_title)
                VALUES (%s, %s)
                ON CONFLICT ({genre_name}_music_id, song_title)
                DO UPDATE SET
                    {genre_name}_music_id = EXCLUDED.{genre_name}_music_id,
                    song_title = EXCLUDED.song_title
                """,
                (music_id, song_title),
            )


def process_and_insert_data(connection, cursor, genre_name):
    create_tables(cursor, genre_name)

    directory_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "requests", "outputs", genre_name)
    )

    with open(f"{directory_path}/{genre_name}_all.json", "r") as file:
        json_content = json.load(file)

    extracted_data = []
    for entry in json_content:
        title = entry.get("result", {}).get("title", "")
        html_content = entry.get("result", {}).get("html", "")

        decoded_title = html.unescape(title)
        decoded_html_content = html.unescape(html_content)

        match_label = re.search(
            r'<a class title="([^"]+)" href="/label/', decoded_html_content
        )
        label_name = match_label.group(1) if match_label else ""
        end_pos = decoded_html_content.find(
            "</a>", decoded_html_content.find('<a class title="')
        )
        start_pos = decoded_html_content.find(">", end_pos + 4) + 1
        end_next_pos = decoded_html_content.find("</a>", start_pos)
        label_issue = (
            decoded_html_content[start_pos:end_next_pos] if end_pos != -1 else ""
        )

        song_titles = extract_song_titles_refined(decoded_html_content)

        if decoded_title:
            artist, _, project_title = decoded_title.partition(":")
            extracted_data.append(
                {
                    "artist": artist.strip(),
                    "project_title": project_title.strip(),
                    "label_name": label_name,
                    "label_issue": label_issue,
                    "song_titles": song_titles,
                }
            )

    # Database operations
    for record in extracted_data:
        insert_data(cursor, genre_name, record)

    connection.commit()


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

cursor.close()
connection.close()
