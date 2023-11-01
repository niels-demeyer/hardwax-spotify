import sys
import os
import psycopg2

# Adding the parent directory of the config module to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config import config


def database_exists(cur, db_name):
    """Check if a database exists."""
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (db_name,))
    return cur.fetchone() is not None


def create_database(cur, conn, db_name):
    """Create a new PostgreSQL database."""
    # Set the connection to autocommit mode
    conn.autocommit = True

    if not database_exists(cur, db_name):
        cur.execute(f"CREATE DATABASE {db_name};")
        print(f"Database {db_name} created successfully.")
    else:
        print(f"Database {db_name} already exists.")

    # Reset the connection to its original autocommit state
    conn.autocommit = False


def fetch_all_genres(cur):
    """Fetch all unique genres from the spotify_data_songs table."""
    cur.execute("SELECT DISTINCT genre FROM spotify_data_songs;")
    return [row[0] for row in cur.fetchall()]


def fetch_data_by_genre(cur, genre, offset=0, limit=11000):
    """Fetch data by genre with offset and limit."""
    cur.execute(
        """
        SELECT genre, artist, song, album, artist_id, song_id, album_id 
        FROM spotify_data_songs 
        WHERE genre = %s 
        LIMIT %s OFFSET %s;
    """,
        (genre, limit, offset),
    )
    return cur.fetchall()


def create_genre_table(cur, genre, counter):
    """Create a new table for the genre with a counter."""
    table_name = f"{genre}_{counter}"
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            genre VARCHAR(255),
            artist VARCHAR(255),
            song VARCHAR(255),
            album VARCHAR(255),
            artist_id VARCHAR(255),
            song_id VARCHAR(255),
            album_id VARCHAR(255),
            UNIQUE(genre, artist, song)
        );
    """
    )
    return table_name


def insert_data_into_genre_table(cur, table_name, data):
    """Insert data into the genre table and ignore duplicates."""
    cur.executemany(
        f"""
        INSERT INTO {table_name} (
            genre, artist, song, album, artist_id, song_id, album_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (genre, artist, song) DO NOTHING;
    """,
        data,
    )


def main():
    # Connect to the default database
    default_conn = psycopg2.connect(
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
    )
    default_cur = default_conn.cursor()
    print("Connected to the default database")

    # Create new database or connect if it already exists
    new_db_name = "hardwax_spotify"
    create_database(default_cur, default_conn, new_db_name)

    # Step 1: Fetch all genres from the default database
    genres = fetch_all_genres(default_cur)

    # Connect to the new database
    new_db_conn = psycopg2.connect(
        dbname=new_db_name,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
    )
    new_db_cur = new_db_conn.cursor()
    print(f"Connected to the database {new_db_name}")

    # Step 2, 3, 4: For each genre, fetch the data and create tables as needed
    for genre in genres:
        offset = 0
        counter = 1
        while True:
            data = fetch_data_by_genre(default_cur, genre, offset)
            if not data:
                break

            table_name = create_genre_table(new_db_cur, genre, counter)
            insert_data_into_genre_table(new_db_cur, table_name, data)

            offset += 11000
            counter += 1

    new_db_conn.commit()
    print("Data migration completed!")

    # Close all cursors and connections
    new_db_cur.close()
    new_db_conn.close()
    default_cur.close()
    default_conn.close()


if __name__ == "__main__":
    main()
