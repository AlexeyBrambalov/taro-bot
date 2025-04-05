import os
import logging
import random
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackContext, CallbackQueryHandler,
    MessageHandler, ConversationHandler, filters
)
from telegram.constants import ParseMode
import google.generativeai as genai
from tarot_cards import tarot_cards
from ai_prompt import generate_tarot_prompt
from horoscope import register_horoscope_handlers

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL2")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini AI client
genai.configure(api_key=GEMINI_API_KEY)

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ConversationHandler states
GENDER, NAME = range(2)

# Database functions
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

# /start command
async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user

    welcome_text = f"""
    ✨ Добро пожаловать, {user.first_name}! ✨

    Я - ваш персональный бот-предсказатель с тремя основными функциями:

    🃏 Обычное гадание на картах Таро (/tarot)
    - Выбираю случайную карту из колоды
    - Даю её классическое толкование
    - Добавляю AI-интерпретацию

    🧙 Персональное гадание Таро (/personal_tarot)
    - Сохраняю ваше имя и пол для персонализации
    - Анализирую карту с учётом ваших особенностей
    - Даю более точное и индивидуальное предсказание

    🌌 Гороскоп (/horoscope [знак зодиака])
    - Составляю ежедневный астропрогноз
    - Анализирую влияние планет
    - Даю практические советы на день

    Выберите одну из функций ниже или используйте команды:
    """
    keyboard = [["/tarot", "/personal_tarot", "/horoscope"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
    )
    
    user_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    add_user_to_db(user_id, username, first_name, last_name)

# /tarot command
async def tarot(update: Update, context: CallbackContext, name=None, gender=None) -> None:
    random.shuffle(tarot_cards)
    card = random.choice(tarot_cards)
    caption = f"{name or 'Ваша'} карта: *{card['name']}*\n\n{card['meaning']}\n\n⏳ Скоро появится предсказание по вашей карте..."

    try:
        with open(card['image_path'], 'rb') as image_file:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_file, caption=caption, parse_mode=ParseMode.MARKDOWN)
    except FileNotFoundError:
        await update.message.reply_text(f"Изображение карты {card['name']} не найдено.")

    await send_ai_insight(update, card, name, gender)

    user = update.message.from_user
    add_user_to_db(user.id, user.username, user.first_name, user.last_name)

# AI interpretation
async def send_ai_insight(update: Update, card, name=None, gender=None):
    prompt = generate_tarot_prompt(card['name'], name, gender)
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-001')
        response = model.generate_content(prompt)
        text_response = response.text.lstrip("#").strip()
        await update.message.reply_text(text_response, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        await update.message.reply_text("Ошибка при генерации AI-интерпретации.")

# PERSONAL TAROT FLOW
async def personal_tarot_start(update: Update, context: CallbackContext) -> int:
    user_data = get_user_from_db(update.message.from_user.id)
    if user_data and user_data[0] and user_data[1]:
        await tarot(update, context, name=user_data[0], gender=user_data[1])
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("Мужчина", callback_data='male'),
         InlineKeyboardButton("Женщина", callback_data='female')]
    ]
    await update.message.reply_text("Выберите ваш пол:", reply_markup=InlineKeyboardMarkup(keyboard))
    return GENDER

async def gender_choice(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['gender'] = 'Мужчина' if query.data == 'male' else 'Женщина'
    await query.message.reply_text("Введите ваше имя:")
    return NAME

async def name_input(update: Update, context: CallbackContext) -> int:
    name = update.message.text
    gender = context.user_data.get('gender')
    user = update.message.from_user

    add_user_to_db(user.id, user.username, user.first_name, user.last_name, name, gender)
    await tarot(update, context, name, gender)
    return ConversationHandler.END

# Main bot setup
def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Basic commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("tarot", tarot))

    # Personal tarot with conversation flow
    personal_tarot_conv = ConversationHandler(
        entry_points=[CommandHandler("personal_tarot", personal_tarot_start)],
        states={
            GENDER: [CallbackQueryHandler(gender_choice)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_input)],
        },
        fallbacks=[],
    )
    application.add_handler(personal_tarot_conv)

    # Horoscope handlers (from horoscope.py)
    register_horoscope_handlers(application)

    # Start polling
    application.run_polling()

if __name__ == '__main__':
    main()
