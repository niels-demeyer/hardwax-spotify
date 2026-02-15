# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import psycopg2
from scrapy.exceptions import DropItem
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

host = os.getenv("DB_HOST")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
dbname = os.getenv("DB_NAME")


class PostgreSQLPipeline(object):
    def __init__(self):
        self.connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            dbname=dbname,  # connect to the scrapy_hardwax database
        )
        self.connection.autocommit = True
        self.cursor = self.connection.cursor()

    def open_spider(self, spider):
        # create the table
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS music_albums (
                id SERIAL PRIMARY KEY,
                artist TEXT,
                album TEXT,
                label TEXT,
                label_issue TEXT,
                genre TEXT,
                track TEXT,
                UNIQUE(artist, album, genre, track)
            )
            """
        )
        self.connection.commit()

    def process_item(self, item, spider):
        self.cursor.execute(
            """
            INSERT INTO music_albums (artist, album, label, label_issue, genre, track)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (artist, album, genre, track) DO NOTHING
            """,
            (
                item.get("artist"),
                item.get("album"),
                item.get("label"),
                item.get("label_issue"),
                spider.name,
                item.get("track"),
            ),
        )
        self.connection.commit()
        return item

    def close_spider(self, spider):
        self.cursor.close()
        self.connection.close()
