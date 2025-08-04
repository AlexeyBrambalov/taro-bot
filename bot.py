import os
import logging
import random
from dotenv import load_dotenv
from types import SimpleNamespace
from telegram import Chat
from telegram.ext import Application, CallbackContext, CommandHandler
import google.generativeai as genai
from tarot_cards import tarot_cards
from ai_prompt import generate_tarot_prompt
from datetime import time
import psycopg2

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL2")

if not TELEGRAM_BOT_TOKEN:
    raise EnvironmentError("TELEGRAM_BOT_TOKEN is not set in .env")

if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY is not set in .env")

if not DATABASE_URL:
    raise EnvironmentError("DATABASE_URL2 is not set in .env")

# Configure Gemini AI client
genai.configure(api_key=GEMINI_API_KEY)

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# --- Database functions ---
def subscribe_user(user):
    """Add/update user and set subscribed=True"""
    try:
        with psycopg2.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                query = """
                    INSERT INTO users (user_id, username, first_name, last_name, name, gender, start_date, last_visited, subscribed)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, TRUE)
                    ON CONFLICT (user_id)
                    DO UPDATE SET 
                        username = EXCLUDED.username, 
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        name = COALESCE(EXCLUDED.name, users.name),
                        gender = COALESCE(EXCLUDED.gender, users.gender),
                        last_visited = CURRENT_TIMESTAMP,
                        subscribed = TRUE;
                """
                cursor.execute(
                    query,
                    (
                        user.id,
                        user.username,
                        user.first_name,
                        user.last_name,
                        None,
                        None,
                    ),
                )
                logger.info(f"User {user.username} subscribed.")
    except Exception as e:
        logger.error(f"Database error (subscribe): {e}")


def unsubscribe_user(user_id):
    """Mark user as unsubscribed"""
    try:
        with psycopg2.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET subscribed = FALSE WHERE user_id = %s",
                    (user_id,),
                )
                logger.info(f"User {user_id} unsubscribed.")
    except Exception as e:
        logger.error(f"Database error (unsubscribe): {e}")


def get_subscribers():
    """Return list of subscribed user_ids"""
    try:
        with psycopg2.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT user_id FROM users WHERE subscribed = TRUE")
                rows = cursor.fetchall()
                return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"Database error (get_subscribers): {e}")
        return []


# --- Tarot logic ---
async def tarot(update, context, name=None, gender=None):
    random.shuffle(tarot_cards)
    card = random.choice(tarot_cards)

    try:
        prompt = generate_tarot_prompt(card["name"], name, gender)
        model = genai.GenerativeModel("gemini-2.0-flash-001")
        response = await model.generate_content_async(prompt)
        poetic_text = response.text.strip()

        with open(card["image_path"], "rb") as image_file:
            caption = (
                f"{card['name']}\n"
                f"{card['category'].capitalize()} — {card['meaning']}\n\n"
                f"«{poetic_text}»"
            )

            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=image_file,
                caption=caption,
                parse_mode=None,
            )

    except FileNotFoundError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Изображение карты {card['name']} не найдено.",
        )
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Ошибка при генерации предсказания.",
        )


# --- Subscription Commands ---
async def subscribe(update, context):
    subscribe_user(update.effective_user)
    await update.message.reply_text(
        "✅ You are now subscribed to daily tarot readings."
    )


async def unsubscribe(update, context):
    unsubscribe_user(update.effective_chat.id)
    await update.message.reply_text(
        "❌ You are unsubscribed from daily tarot readings."
    )


# --- Daily Tarot Job ---
async def daily_tarot_job(context: CallbackContext):
    subscribers = get_subscribers()
    if not subscribers:
        logger.info("No subscribers for daily tarot.")
        return

    for chat_id in subscribers:
        try:
            fake_update = SimpleNamespace(
                message=None, effective_chat=Chat(id=chat_id, type="private")
            )
            await tarot(fake_update, context)
        except Exception as e:
            logger.error(f"Failed to send tarot to {chat_id}: {e}")


def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("tarot", tarot))  # manual tarot draw

    # Schedule daily tarot at 09:00
    application.job_queue.run_daily(
        callback=daily_tarot_job,
        time=time(hour=9, minute=0),
    )

    application.run_polling()


if __name__ == "__main__":
    main()
