from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext
from db import add_user_to_db  # assuming you move DB logic into db.py

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

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    user_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    add_user_to_db(user_id, username, first_name, last_name)
