import os
import logging
import random
from dotenv import load_dotenv
from types import SimpleNamespace
from telegram import Chat, User
from telegram.ext import Application, CallbackContext
from telegram.constants import ParseMode
import google.generativeai as genai
from tarot_cards import tarot_cards
from ai_prompt import generate_tarot_prompt
from utils import sanitize_markdown
from datetime import time

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
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
                parse_mode=None,  # disable markdown to preserve symbols
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


async def daily_tarot_job(context: CallbackContext):
    chat_id = os.getenv("DAILY_TAROT_CHAT_ID")
    if not chat_id:
        logger.warning("DAILY_TAROT_CHAT_ID not set.")
        return

    chat_id = int(chat_id)

    # Simulated Update object for job queue
    fake_update = SimpleNamespace(
        message=None, effective_chat=Chat(id=chat_id, type="private")
    )

    await tarot(fake_update, context)


def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Schedule daily tarot at 09:00
    application.job_queue.run_daily(
        callback=daily_tarot_job,
        time=time(hour=9, minute=0),
    )

    application.run_polling()


if __name__ == "__main__":
    main()
