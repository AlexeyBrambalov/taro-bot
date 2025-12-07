import os
import logging
import random
import asyncio
from dotenv import load_dotenv
from datetime import time, datetime
from types import SimpleNamespace

from telegram.ext import Application, CallbackContext, CommandHandler
import google.generativeai as genai
import psycopg2
import pytz

from tarot_cards import tarot_cards
from ai_prompt import generate_tarot_prompt


# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL2")

if not TELEGRAM_BOT_TOKEN:
    raise EnvironmentError("TELEGRAM_BOT_TOKEN missing")
if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY missing")
if not DATABASE_URL:
    raise EnvironmentError("DATABASE_URL2 missing")

genai.configure(api_key=GEMINI_API_KEY)

# Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger("TarotBot")


def get_utc_hour_for_timezone(tz_name, local_hour=10):
    """
    Calculate UTC hour for a given timezone's local hour.
    """
    try:
        tz = pytz.timezone(tz_name)
        # Create a naive datetime for today at the target local hour
        now = datetime.now()
        local_time = tz.localize(
            datetime(now.year, now.month, now.day, local_hour, 0, 0)
        )
        # Convert to UTC
        utc_time = local_time.astimezone(pytz.UTC)
        return utc_time.hour
    except Exception as e:
        logger.warning(
            f"Error calculating UTC hour for {tz_name}, defaulting to {local_hour}: {e}"
        )
        return local_hour


# --- DB Helpers ---
def subscribe_user(user):
    """Mark subscribed & update last seen + username info."""
    query = """
        INSERT INTO users (user_id, username, first_name, last_name, start_date, last_visited, subscribed)
        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, TRUE)
        ON CONFLICT (user_id)
        DO UPDATE SET
            username = EXCLUDED.username,
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            last_visited = CURRENT_TIMESTAMP,
            subscribed = TRUE;
    """
    try:
        with psycopg2.connect(DATABASE_URL) as con:
            with con.cursor() as cur:
                cur.execute(
                    query, (user.id, user.username, user.first_name, user.last_name)
                )
        logger.info(f"User {user.id} subscribed ✅")
    except Exception as e:
        logger.error(f"DB subscribe error: {e}")


def unsubscribe_user(user_id):
    """Set subscribed = FALSE."""
    try:
        with psycopg2.connect(DATABASE_URL) as con:
            with con.cursor() as cur:
                cur.execute(
                    "UPDATE users SET subscribed=FALSE WHERE user_id=%s", (user_id,)
                )
        logger.info(f"User {user_id} unsubscribed ❌")
    except Exception as e:
        logger.error(f"DB unsubscribe error: {e}")


def get_subscribers_by_timezone():
    """Return dict: timezone -> [user_ids]"""
    try:
        with psycopg2.connect(DATABASE_URL) as con:
            with con.cursor() as cur:
                cur.execute("""
                    SELECT COALESCE(timezone, 'Europe/London'), array_agg(user_id)
                    FROM users WHERE subscribed = TRUE
                    GROUP BY COALESCE(timezone, 'Europe/London')
                """)
                rows = cur.fetchall()
                return {row[0]: row[1] for row in rows}
    except Exception as e:
        logger.error(f"DB fetch timezone error: {e}")
        return {}


# --- Tarot Logic ---
async def generate_tarot_text(card, name=None, gender=None):
    prompt = generate_tarot_prompt(card["name"], name, gender)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = await model.generate_content_async(prompt)
    return response.text.strip()


async def send_tarot_to_chat(chat_id, context):
    random.shuffle(tarot_cards)
    card = random.choice(tarot_cards)

    try:
        poetic = await generate_tarot_text(card)
        caption = (
            f"{card['name']}\n"
            f"{card['category'].capitalize()} — {card['meaning']}\n\n"
            f"«{poetic}»"
        )

        with open(card["image_path"], "rb") as img:
            await context.bot.send_photo(chat_id=chat_id, photo=img, caption=caption)

    except FileNotFoundError:
        await context.bot.send_message(
            chat_id=chat_id, text=f"No image found for {card['name']}."
        )
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        await context.bot.send_message(
            chat_id=chat_id, text="AI error — try again later 😔"
        )


async def tarot(update, context):
    await send_tarot_to_chat(update.effective_chat.id, context)


# --- Commands ---
async def subscribe(update, context):
    subscribe_user(update.effective_user)
    await update.message.reply_text("✅ Subscribed to daily tarot readings!")


async def unsubscribe(update, context):
    unsubscribe_user(update.effective_chat.id)
    await update.message.reply_text("❌ Unsubscribed from daily tarot readings.")


# --- Daily Background Job ---
async def daily_tarot_job(context: CallbackContext):
    timezone = context.job.data["timezone"]
    tz_list = get_subscribers_by_timezone()
    user_ids = tz_list.get(timezone, [])

    logger.info(f"Sending tarot to {len(user_ids)} users in {timezone}")

    for user_id in user_ids:
        try:
            await send_tarot_to_chat(user_id, context)
            await asyncio.sleep(10)  # prevent AI API rate limit
        except Exception as e:
            logger.error(f"Failed send → {user_id}: {e}")


def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register commands
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("tarot", tarot))

    # Schedule per timezone at their local 10:00 AM (converted to UTC)
    tz_users = get_subscribers_by_timezone()

    for tz_name in tz_users:
        utc_hour = get_utc_hour_for_timezone(tz_name, local_hour=10)

        logger.info(f"Scheduling {tz_name} at {utc_hour}:00 UTC (10:00 local)")

        # Schedule daily job at the calculated UTC hour
        application.job_queue.run_daily(
            daily_tarot_job,
            time=time(hour=utc_hour, minute=0, tzinfo=pytz.UTC),
            data={"timezone": tz_name},
            name=f"daily_tarot_{tz_name}",
        )

    logger.info("Bot started ✅✨")
    application.run_polling()


if __name__ == "__main__":
    main()
