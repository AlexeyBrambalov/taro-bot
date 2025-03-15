import os
import logging
import random
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up PostgreSQL connection
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    return conn

# Command to start the bot
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hello! I am your Tarot bot.')

# Command to fetch a random Tarot card from the database
def tarot(update: Update, context: CallbackContext) -> None:
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Query to fetch a random card
    cursor.execute("SELECT name, meaning FROM cards ORDER BY RANDOM() LIMIT 1")
    card = cursor.fetchone()

    # If a card is found, send its name and meaning
    if card:
        card_name, card_meaning = card
        update.message.reply_text(f"Today's card: {card_name}\nMeaning: {card_meaning}")
    else:
        update.message.reply_text("Sorry, there are no cards in the database.")

    # Close the database connection
    cursor.close()
    conn.close()

# Main function to run the bot
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("tarot", tarot))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
