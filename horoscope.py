import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler
import google.generativeai as genai
from ai_prompt import generate_horoscope_prompt

logger = logging.getLogger(__name__)

ZODIAC_SIGNS = [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"
]

async def horoscope_command(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton(sign, callback_data=f'zodiac_{sign}')] for sign in ZODIAC_SIGNS
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите ваш знак зодиака:", reply_markup=reply_markup)

async def zodiac_selected(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    sign = query.data.replace('zodiac_', '')

    await query.message.reply_text(f"🔮 Подготавливаю гороскоп для *{sign}*...", parse_mode=ParseMode.MARKDOWN)
    prompt = generate_horoscope_prompt(sign)
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-001')
        response = model.generate_content(prompt)
        text_response = response.text.lstrip("#").strip()
        await query.message.reply_text(f"🌟 Гороскоп для *{sign}*:\n\n{text_response}", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        await query.message.reply_text("Ошибка при генерации гороскопа.")

def register_horoscope_handlers(application):
    application.add_handler(CommandHandler("horoscope", horoscope_command))
    application.add_handler(CallbackQueryHandler(zodiac_selected, pattern=r'^zodiac_'))
