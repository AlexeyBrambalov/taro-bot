import os
import logging
import random
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Retrieve environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL2")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini AI client
genai.configure(api_key=GEMINI_API_KEY)

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Tarot card data
tarot_cards = [
    # {"name": "Смерть", "meaning": "Трансформация и завершение.", "image_path": "images/death.jpg"},
    # {"name": "Дьявол", "meaning": "Искушение и материализм.", "image_path": "images/devil.jpg"},
    # {"name": "10 мечей", "meaning": "Предательство и завершение сложного периода.", "image_path": "images/ten-swords.jpg"},
    # {"name": "Три чаши", "meaning": "Празднование и дружба.", "image_path": "images/three-cups.jpg"},
    # {"name": "Башня", "meaning": "Потрясение и внезапные перемены.", "image_path": "images/tower.jpg"},
    {"name": "Туз пентаклей", "meaning": "Новые финансовые возможности и стабильность.", "image_path": "images/ace-pentacles.jpg"},
    {"name": "Иерофант", "meaning": "Традиции, духовность и наставничество.", "image_path": "images/hierophant.jpg"},
    {"name": "Любовь", "meaning": "Гармония, романтические отношения и союз.", "image_path": "images/love.jpg"},
    {"name": "Мир", "meaning": "Спокойствие, завершение и целостность.", "image_path": "images/peace.jpg"},
    {"name": "Звезда", "meaning": "Надежда, вдохновение и исполнение желаний.", "image_path": "images/star.jpg"},
]

def add_user_to_db(user_id, username, first_name, last_name):
    """Adds or updates a user in the database."""
    try:
        with psycopg2.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                insert_query = """
                    INSERT INTO users (user_id, username, first_name, last_name, start_date, last_visited)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id)
                    DO UPDATE SET username = EXCLUDED.username, first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name, last_visited = CURRENT_TIMESTAMP;
                """
                cursor.execute(insert_query, (user_id, username, first_name, last_name))
                logger.info(f"User {username} added/updated in the database.")
    except Exception as e:
        logger.error(f"Database error: {e}")

async def tarot(update: Update, context: CallbackContext) -> None:
    """Handles the /tarot command."""
    random.shuffle(tarot_cards)
    card = random.choice(tarot_cards)
    caption = f"Ваша карта: *{card['name']}*\n\n{card['meaning']}\n\n⏳ Скоро появится предсказание по вашей карте..."
    
    try:
        with open(card['image_path'], 'rb') as image_file:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_file, caption=caption, parse_mode=ParseMode.MARKDOWN)
    except FileNotFoundError:
        await update.message.reply_text(f"Изображение карты {card['name']} не найдено.")
    
    await send_ai_insight(update, card)

async def personal_tarot(update: Update, context: CallbackContext) -> None:
    """Handles the /personal_tarot command."""
    keyboard = [[InlineKeyboardButton("Мужчина", callback_data='male'), InlineKeyboardButton("Женщина", callback_data='female')]]
    await update.message.reply_text("Выберите ваш пол:", reply_markup=InlineKeyboardMarkup(keyboard))

async def gender_choice(update: Update, context: CallbackContext) -> None:
    """Handles gender selection for personalized Tarot reading."""
    query = update.callback_query
    await query.answer()
    context.user_data['gender'] = 'Мужчина' if query.data == 'male' else 'Женщина'
    await query.message.reply_text("Введите ваше имя:")

async def name_input(update: Update, context: CallbackContext) -> None:
    """Handles name input for personalized Tarot reading."""
    name = update.message.text
    gender = context.user_data.get('gender', 'неизвестного пола')
    card = random.choice(tarot_cards)
    caption = f"{name}, ваша карта: *{card['name']}*\n\n{card['meaning']}"
    
    try:
        with open(card['image_path'], 'rb') as image_file:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_file, caption=caption, parse_mode=ParseMode.MARKDOWN)
    except FileNotFoundError:
        await update.message.reply_text(f"{name}, изображение карты {card['name']} не найдено.")
    
    await send_ai_insight(update, card, name, gender)

async def send_ai_insight(update: Update, card, name=None, gender=None):
    """Generates and sends an AI-based Tarot interpretation."""
    prompt = f"""Напиши толкование карты Таро *{card['name']}* {'для ' + gender + ' по имени ' + name if name else ''}в следующем стиле (используется колода *Heaven and Earth*):
    🔮 *{card['name']}* – [Краткое описание карты, её основное значение]

    ✨ *Символика и толкование:*
    [Подробное описание карты, её символика и значение]

    *Значение в различных аспектах жизни:*
    ❤️  *Любовь:* 
    [Толкование карты в любовных вопросах]

    💼 *Работа:* 
    [Значение карты в сфере карьеры]

    💰 *Финансы:* 
    [Как карта влияет на материальную сторону жизни]

    📝 *Совет карты:*
    [Практический совет от карты]

    ⚠️ *Предупреждение:*
    [Возможные негативные аспекты или предостережения]

    Пожалуйста, учитывай, что максимальная длина текста для одного сообщения – 4096 символов.
    Используй насыщенный, образный язык, чтобы передать энергию и смысл карты.
    Включай метафоры и сравнения, чтобы сделать толкование более понятным и запоминающимся.
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-001')  
        response = model.generate_content(prompt)
        await update.message.reply_text(response.text.lstrip("#").strip(), parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        await update.message.reply_text("Произошла ошибка при генерации AI-интерпретации.")

async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    
    keyboard = [["/tarot", "/personal_tarot"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        f'Привет, {user.first_name}! Я твой бот Таро. Выбери один из вариантов ниже:',
        reply_markup=reply_markup
    )
    
    # Добавляем пользователя в базу данных
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    first_name = update.message.from_user.first_name
    last_name = update.message.from_user.last_name
    add_user_to_db(user_id, username, first_name, last_name)

def main():
    """Main function to run the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("tarot", tarot))
    application.add_handler(CommandHandler("personal_tarot", personal_tarot))
    application.add_handler(CallbackQueryHandler(gender_choice))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, name_input))
    
    application.run_polling()

if __name__ == '__main__':
    main()
