import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

cards = [
    ("The Fool", "New beginnings, spontaneity, adventure."),
    ("The Magician", "Power, skill, concentration."),
    ("The High Priestess", "Intuition, mystery, wisdom."),
    ("The Empress", "Fertility, nature, abundance."),
    ("The Emperor", "Authority, stability, structure."),
    ("The Lovers", "Love, relationships, choices."),
    ("The Chariot", "Willpower, victory, determination."),
    ("Death", "Endings, transformation, new beginnings."),
    ("The Tower", "Sudden change, chaos, revelation."),
    ("The Star", "Hope, inspiration, renewal."),
]

conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cursor = conn.cursor()

cursor.executemany("INSERT INTO cards (name, meaning) VALUES (%s, %s)", cards)
conn.commit()
conn.close()

print("Tarot cards added to the database.")