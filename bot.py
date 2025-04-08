import os
import logging
import random
import re
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
from start import start
from db import add_user_to_db, get_user_from_db
from utils import sanitize_markdown

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
        raw_text = response.text.lstrip("#").strip()
        safe_text = sanitize_markdown(raw_text)
        await update.message.reply_text(safe_text, parse_mode=ParseMode.MARKDOWN)
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
