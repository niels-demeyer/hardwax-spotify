import os
from dotenv import load_dotenv
import pprint
import psycopg2
from psycopg2.extras import DictCursor


load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Establish a connection to the database
conn = psycopg2.connect(
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASS,
    host=DB_HOST,
    port=DB_PORT,
)

# Create a cursor using the DictCursor
cursor = conn.cursor(cursor_factory=DictCursor)


def select_all_from_table_as_dict(table_name):
    # Execute a SQL query to select all records from the table
    cursor.execute(f"SELECT * FROM {table_name}")

    # Fetch all the records
    records = cursor.fetchall()

    # Return the fetched records
    return records


def select_distinct_genres(cursor, table_name="spotify_data_songs"):
    # Execute a SQL query to select distinct genres from the table
    cursor.execute(f"SELECT DISTINCT genre FROM {table_name}")

    # Fetch all the records
    records = cursor.fetchall()

    # Extract the first element from each tuple and convert the list to a tuple
    genres = tuple(record[0] for record in records)

    # Return the fetched records
    return genres


def get_items_by_genre(genre, table_name="spotify_data_songs"):
    # Execute a SQL query to select all records from the table
    cursor.execute(f"SELECT * FROM {table_name} WHERE genre = '{genre}'")

    # Fetch all the records
    records = cursor.fetchall()

    # Return the fetched records
    return records


def create_genre_tables(cursor, conn, genre):
    # Replace hyphens with underscores in the genre name
    genre = genre.replace("-", "_")

    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {genre} 
        (
            id SERIAL PRIMARY KEY, 
            genre VARCHAR(255), 
            artist VARCHAR(255), 
            song VARCHAR(255), 
            album VARCHAR(255), 
            artist_id VARCHAR(255), 
            song_id VARCHAR(255), 
            album_id VARCHAR(255),
            UNIQUE(id, genre, artist, song)
        )
        """
    )
    conn.commit()


def insert_into_genre_tables(cursor, conn, genre, items):
    # Replace hyphens with underscores in the genre name
    genre = genre.replace("-", "_")

    # Insert records into the table
    for item in items:
        cursor.execute(
            f"""
            INSERT INTO {genre}
            (id, genre, artist, song, album, artist_id, song_id, album_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id, genre, artist, song) DO NOTHING
            """,
            tuple(item.values()),
        )
        conn.commit()


def split_big_playlist(cursor, conn, genre):
    genre = genre.replace("-", "_")
    # select the count of records for the genre
    cursor.execute(f"SELECT COUNT(*) FROM {genre}")
    len_genre = cursor.fetchone()[0]
    print(f"the length of {genre} is:", len_genre)
    cursor.execute(f"SELECT * FROM {genre} ORDER BY id")
    records = cursor.fetchall()

    # establish a new connection to the "hardwax_spotify" database
    new_conn = psycopg2.connect(
        database="hardwax_spotify",
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT,
    )
    new_cursor = new_conn.cursor()
    if len_genre > 11000:
        splits = int(len_genre / 11000) + 1
        print(f"the number of splits is: {splits}")
        for i in range(splits):
            split_records = records[i * 11000 : (i + 1) * 11000]
            new_cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {genre}_{i} 
                (
                    id SERIAL PRIMARY KEY, 
                    genre VARCHAR(255), 
                    artist VARCHAR(255), 
                    song VARCHAR(255), 
                    album VARCHAR(255), 
                    artist_id VARCHAR(255), 
                    song_id VARCHAR(255), 
                    album_id VARCHAR(255),
                    UNIQUE(id, genre, artist, song)
                )
                """
            )
            new_conn.commit()
            for record in split_records:
                new_cursor.execute(
                    f"""
                    INSERT INTO {genre}_{i}
                    (id, genre, artist, song, album, artist_id, song_id, album_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id, genre, artist, song) DO NOTHING
                    """,
                    tuple(record),
                )
                new_conn.commit()
    else:
        print(f"the number of splits is: 1")
        new_cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {genre}_0 
            (
                id SERIAL PRIMARY KEY, 
                genre VARCHAR(255), 
                artist VARCHAR(255), 
                song VARCHAR(255), 
                album VARCHAR(255), 
                artist_id VARCHAR(255), 
                song_id VARCHAR(255), 
                album_id VARCHAR(255),
                UNIQUE(id, genre, artist, song)
            )
            """
        )
        new_conn.commit()
        for record in records:
            new_cursor.execute(
                f"""
                INSERT INTO {genre}_0
                (id, genre, artist, song, album, artist_id, song_id, album_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id, genre, artist, song) DO NOTHING
                """,
                tuple(record),
            )
            new_conn.commit()


def main(cursor, conn):
    # Select all records from the music_albums table
    records = select_all_from_table_as_dict("spotify_data_songs")
    genres = select_distinct_genres(cursor, "spotify_data_songs")
    for genre in genres:
        create_genre_tables(cursor, conn, genre)
        items = get_items_by_genre(genre, "spotify_data_songs")
        insert_into_genre_tables(cursor, conn, genre, items)
        split_big_playlist(cursor, conn, genre)


if __name__ == "__main__":
    main(cursor, conn)


cursor.close()
conn.close()
