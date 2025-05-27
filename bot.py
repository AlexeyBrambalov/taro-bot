import os
import logging
import random
from dotenv import load_dotenv
from types import SimpleNamespace
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat, User
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)
from telegram.constants import ParseMode
import google.generativeai as genai
from tarot_cards import tarot_cards
from ai_prompt import generate_tarot_prompt
from horoscope import register_horoscope_handlers
from start import start
from db import add_user_to_db, get_user_from_db
from utils import sanitize_markdown
from datetime import time

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL2")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_BOT_TOKEN:
    raise EnvironmentError("TELEGRAM_BOT_TOKEN is not set in .env")

if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY is not set in .env")

# Configure Gemini AI client
genai.configure(api_key=GEMINI_API_KEY)

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ConversationHandler states
GENDER, NAME = range(2)


# /tarot command
async def tarot(
    update: Update, context: CallbackContext, name=None, gender=None
) -> None:
    random.shuffle(tarot_cards)
    card = random.choice(tarot_cards)
    category = card["category"]

    caption = f"{name or 'Ваша'} карта: *{card['name']}*\n\nКатегория: *{category}*\n\n{card['meaning']}\n\n⏳ Скоро появится предсказание по вашей карте..."

    try:
        with open(card["image_path"], "rb") as image_file:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=image_file,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
            )
    except FileNotFoundError:
        if update.message:
            await update.message.reply_text(
                f"Изображение карты {card['name']} не найдено."
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Изображение карты {card['name']} не найдено.",
            )

    await send_ai_insight(update, context, card, name, gender)

    if update.message and update.message.from_user:
        user = update.message.from_user
        add_user_to_db(user.id, user.username, user.first_name, user.last_name)


async def daily_tarot_job(context: CallbackContext):
    chat_id = os.getenv("DAILY_TAROT_CHAT_ID")
    if not chat_id:
        logger.warning("DAILY_TAROT_CHAT_ID not set.")
        return

    chat_id = int(chat_id)

    # Fake Message and Update for job queue
    class FakeMessage:
        from_user = User(id=chat_id, first_name="Daily", is_bot=False)
        chat = Chat(id=chat_id, type="private")

        async def reply_text(self, text, **kwargs):
            await context.bot.send_message(chat_id=chat_id, text=text, **kwargs)

    fake_update = SimpleNamespace(
        message=FakeMessage(), effective_chat=Chat(id=chat_id, type="private")
    )

    await tarot(fake_update, context)


# AI interpretation
async def send_ai_insight(
    update: Update, context: CallbackContext, card, name=None, gender=None
):
    prompt = generate_tarot_prompt(card["name"], name, gender)
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-001")
        response = await model.generate_content_async(prompt)
        raw_text = response.text.lstrip("#").strip()
        safe_text = sanitize_markdown(raw_text)

        if update.message:
            await update.message.reply_text(safe_text, parse_mode=ParseMode.MARKDOWN)
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=safe_text,
                parse_mode=ParseMode.MARKDOWN,
            )

    except Exception as e:
        logger.error(f"AI generation error: {e}")
        error_text = "Ошибка при генерации AI-интерпретации."

        if update.message:
            await update.message.reply_text(error_text)
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=error_text
            )


# PERSONAL TAROT FLOW
async def personal_tarot_start(update: Update, context: CallbackContext) -> int:
    user_data = get_user_from_db(update.message.from_user.id)
    if user_data and user_data[0] and user_data[1]:
        await tarot(update, context, name=user_data[0], gender=user_data[1])
        return ConversationHandler.END

    keyboard = [
        [
            InlineKeyboardButton("Мужчина", callback_data="male"),
            InlineKeyboardButton("Женщина", callback_data="female"),
        ]
    ]
    await update.message.reply_text(
        "Выберите ваш пол:", reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return GENDER


async def gender_choice(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["gender"] = "Мужчина" if query.data == "male" else "Женщина"
    await query.message.reply_text("Введите ваше имя:")
    return NAME


async def name_input(update: Update, context: CallbackContext) -> int:
    name = update.message.text
    gender = context.user_data.get("gender")
    user = update.message.from_user

    add_user_to_db(
        user.id, user.username, user.first_name, user.last_name, name, gender
    )
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

    register_horoscope_handlers(application)

    application.job_queue.run_daily(
        callback=daily_tarot_job,
        time=time(hour=9, minute=0),
    )

    # Start bot
    application.run_polling()


if __name__ == "__main__":
    main()
