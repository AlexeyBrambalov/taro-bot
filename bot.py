import os
import logging
import random
import psycopg2
from psycopg2 import sql
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from dotenv import load_dotenv
import google.generativeai as genai 
from telegram.constants import ParseMode

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL2")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini AI client
genai.configure(api_key=GEMINI_API_KEY) 

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# List of Tarot cards and their meanings
tarot_cards = [
    {
        "name": "Смерть",
        "meaning": "Означает трансформацию и завершение, обозначая конец одного этапа и начало нового.",
        "image_path": "images/death.jpg"
    },
    {
        "name": "Дьявол",
        "meaning": "Представляет искушение и материализм, предостерегая от излишеств и зависимости.",
        "image_path": "images/devil.jpg"
    },
    {
        "name": "10 мечей",
        "meaning": "Означает предательство и дно, указывая на завершение сложного периода",
        "image_path": "images/ten-swords.jpg"
    },
    {
        "name": "Три чаши",
        "meaning": "Обозначает празднование и дружбу, побуждая к радости и единению",
        "image_path": "images/three-cups.jpg"
    },
    {
        "name": "Башня",
        "meaning": "Символизирует потрясение и откровение, указывая на внезапные перемены и пробуждение.",
        "image_path": "images/tower.jpg"
    },
]

def add_user_to_db(user_id, username, first_name, last_name):
    try:
        connection = psycopg2.connect(DATABASE_URL)
        cursor = connection.cursor()
        insert_query = """
            INSERT INTO users (user_id, username, first_name, last_name, start_date, last_visited)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id)
            DO UPDATE SET
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                last_visited = CURRENT_TIMESTAMP;
        """
        cursor.execute(insert_query, (user_id, username, first_name, last_name))
        connection.commit()
        cursor.close()
        connection.close()
        logger.info(f"User {username} added to the database.")
    except Exception as e:
        logger.error(f"Error adding user to database: {e}")

# Command to start the bot
async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    await update.message.reply_text(f'Hello, {user.first_name}! I am your Tarot bot.')
    # Add user to the database
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    first_name = update.message.from_user.first_name
    last_name = update.message.from_user.last_name
    add_user_to_db(user_id, username, first_name, last_name)

# Command to fetch a random Tarot card
async def tarot(update: Update, context: CallbackContext) -> None:
    card = random.choice(tarot_cards)
    caption = f"*{card['name']}*\n\n{card['meaning']}"
    try:
        with open(card['image_path'], 'rb') as image_file:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_file, caption=caption, parse_mode=ParseMode.MARKDOWN)
    except FileNotFoundError:
        await update.message.reply_text(f"Image for {card['name']} not found. Please check the image path.")

    # Generate AI insight
    prompt = f"""Напиши толкование карты Таро *{card['name']}* в следующем стиле:

        *{card['name']}* – [Краткое описание карты, её основное значение]

        *Символика и толкование:*
        [Подробное описание карты, её символика и значение]

        *Значение в различных аспектах жизни:*
        *Любовь:* [Толкование карты в любовных вопросах]
        *Работа:* [Значение карты в сфере карьеры]
        *Финансы:* [Как карта влияет на материальную сторону жизни]

        *Совет карты:*
        [Практический совет от карты]

        *Предупреждение:*
        [Возможные негативные аспекты или предостережения]

        Используй насыщенный, образный язык, чтобы передать энергию и смысл карты.
        Включай метафоры и сравнения, чтобы сделать толкование более понятным и запоминающимся.
        """

    model = genai.GenerativeModel('gemini-2.0-flash-001')  
    response = model.generate_content(prompt)   
    ai_insight = response.text

    await update.message.reply_text(text=f"{ai_insight}", parse_mode=ParseMode.MARKDOWN)

    user_id = update.message.from_user.id
    username = update.message.from_user.username
    first_name = update.message.from_user.first_name
    last_name = update.message.from_user.last_name
    add_user_to_db(user_id, username, first_name, last_name)

# Main function to run the bot
def main():
    # Create the Application instance
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("tarot", tarot))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
