import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL2")

try:
    connection = psycopg2.connect(DATABASE_URL)
    cursor = connection.cursor()

    # Alter table query
    alter_table_query = """
    ALTER TABLE users
    ADD COLUMN name VARCHAR(255),
    ADD COLUMN gender VARCHAR(10) CHECK (gender IN ('Мужчина', 'Женщина'));
    """
    
    cursor.execute(alter_table_query)
    connection.commit()

    print("Database updated successfully!")

except Exception as e:
    print(f"Error: {e}")

finally:
    if connection:
        cursor.close()
        connection.close()
