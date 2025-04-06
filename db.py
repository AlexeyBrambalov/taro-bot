import os
import psycopg2
import logging
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL2")
logger = logging.getLogger(__name__)

def add_user_to_db(user_id, username, first_name, last_name, name=None, gender=None):
    try:
        with psycopg2.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                query = """
                    INSERT INTO users (user_id, username, first_name, last_name, name, gender, start_date, last_visited)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id)
                    DO UPDATE SET 
                        username = EXCLUDED.username, 
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        name = COALESCE(EXCLUDED.name, users.name),
                        gender = COALESCE(EXCLUDED.gender, users.gender),
                        last_visited = CURRENT_TIMESTAMP;
                """
                cursor.execute(query, (user_id, username, first_name, last_name, name, gender))
                logger.info(f"User {username} added/updated in the database.")
    except Exception as e:
        logger.error(f"Database error: {e}")

def get_user_from_db(user_id):
    try:
        with psycopg2.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT name, gender FROM users WHERE user_id = %s", (user_id,))
                return cursor.fetchone()
    except Exception as e:
        logger.error(f"Database error: {e}")
        return None
