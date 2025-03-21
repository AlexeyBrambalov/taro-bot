import os
import logging
import random
import psycopg2
from psycopg2 import sql
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL2")

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# List of Tarot cards and their meanings
tarot_cards = [
    {
        "name": "The Fool",
        "meaning": "Represents new beginnings, spontaneity, and a free spirit.",
        "example": "Embarking on a spontaneous road trip without a set destination, embracing the adventure ahead.",
        "image_path": "images/the-fool.jpg"
    },
    {
        "name": "The Magician",
        "meaning": "Signifies manifestation, resourcefulness, and inspired action.",
        "example": "Utilizing your skills and tools to launch a new business venture successfully.",
        "image_path": "images/the-magician.jpg"
    },
    {
        "name": "The Empress",
        "meaning": "Signifies fertility and nurturing, highlighting abundance and a connection to nature.",
        "example": "Starting a community garden to foster local engagement and growth.",
        "image_path": "images/the-empress.jpg"
    },
    {
        "name": "The Emperor",
        "meaning": "Represents authority, structure, and control.",
        "example": "Taking the lead on a project at work, establishing clear guidelines and expectations.",
        "image_path": "images/the-emperor.jpg"
    },
    {
        "name": "The Hierophant",
        "meaning": "Denotes tradition, spiritual wisdom, and conformity.",
        "example": "Participating in a cultural ceremony to honor ancestral traditions.",
        "image_path": "images/the-hierophant.jpg"
    },
    # ("The Lovers", "Denotes relationships and choices, focusing on love, harmony, and alignment."),
    # ("The Chariot", "Embodies determination and control, motivating you to overcome obstacles."),
    # ("Strength", "Represents courage and resilience, highlighting inner strength and patience."),
    # ("The Hermit", "Signifies introspection and solitude, guiding you to seek inner guidance."),
    # ("Wheel of Fortune", "Symbolizes cycles and destiny, indicating changes and turning points."),
    # ("Justice", "Represents fairness and truth, emphasizing balance and accountability."),
    # ("The Hanged Man", "Denotes suspension and letting go, encouraging a new perspective."),
    # ("Death", "Signifies transformation and endings, marking the end of a phase and the start of a new one."),
    # ("Temperance", "Embodies balance and moderation, advising patience and harmony."),
    # ("The Devil", "Represents temptation and materialism, warning against excess and addiction."),
    # ("The Tower", "Symbolizes upheaval and revelation, indicating sudden change and awakening."),
    # ("The Star", "Denotes hope and inspiration, offering a sense of peace and renewal."),
    # ("The Moon", "Embodies illusion and intuition, cautioning against deception and encouraging trust in your feelings."),
    # ("The Sun", "Represents success and vitality, bringing clarity and joy."),
    # ("Judgement", "Signifies rebirth and inner calling, prompting reflection and renewal."),
    # ("The World", "Denotes completion and accomplishment, celebrating fulfillment and wholeness."),
    # ("Ace of Cups", "Represents new emotional beginnings, offering love and compassion."),
    # ("2 of Cups", "Symbolizes partnership and unity, highlighting mutual attraction and connection."),
    # ("3 of Cups", "Denotes celebration and friendship, encouraging joy and community."),
    # ("4 of Cups", "Signifies contemplation and apathy, suggesting a need to reassess your emotional state."),
    # ("5 of Cups", "Represents regret and loss, urging you to focus on remaining positives."),
    # ("6 of Cups", "Embodies nostalgia and reunion, connecting you to past memories and innocence."),
    # ("7 of Cups", "Denotes choices and illusions, warning against wishful thinking."),
    # ("8 of Cups", "Signifies abandonment and withdrawal, indicating a need to leave behind unfulfilling situations."),
    # ("9 of Cups", "Represents contentment and satisfaction, highlighting gratitude and fulfillment."),
    # ("10 of Cups", "Denotes happiness and emotional fulfillment, emphasizing harmony in relationships."),
    # ("Ace of Pentacles", "Symbolizes new financial opportunities, suggesting prosperity and stability."),
    # ("2 of Pentacles", "Represents balance and adaptability, managing multiple responsibilities with grace."),
    # ("3 of Pentacles", "Denotes teamwork and collaboration, highlighting the value of working together."),
    # ("4 of Pentacles", "Signifies security and control, cautioning against greed and encouraging generosity."),
    # ("5 of Pentacles", "Embodies hardship and insecurity, reminding you to seek support during tough times."),
    # ("6 of Pentacles", "Represents generosity and charity, emphasizing the importance of giving and receiving."),
    # ("7 of Pentacles", "Denotes assessment and patience, encouraging you to evaluate your progress."),
    # ("8 of Pentacles", "Symbolizes diligence and mastery, highlighting the rewards of hard work."),
    # ("9 of Pentacles", "Represents luxury and self-sufficiency, celebrating independence and success."),
    # ("10 of Pentacles", "Denotes legacy and family, focusing on long-term wealth and stability."),
    # ("Ace of Swords", "Signifies new ideas and clarity, encouraging decisive action and truth."),
    # ("2 of Swords", "Embodies choices and indecision, prompting you to confront difficult decisions."),
    # ("3 of Swords", "Represents heartbreak and sorrow, acknowledging pain and the need for healing."),
    # ("4 of Swords", "Denotes rest and recovery, advising a period of relaxation and contemplation."),
    # ("5 of Swords", "Symbolizes conflict and tension, warning against dishonesty and hollow victories."),
    # ("6 of Swords", "Represents transition and moving on, indicating a journey toward better circumstances."),
    # ("7 of Swords", "Denotes secrecy and stealth, cautioning against betrayal and deceit."),
    # ("8 of Swords", "Embodies restriction and limitation, suggesting a need to break free from self-imposed constraints."),
    # ("9 of Swords", "Signifies anxiety and fear, urging you to address your worries and seek support."),
    # ("10 of Swords", "Represents betrayal and rock bottom, indicating the end of a difficult period."),
    # ("Ace of Wands", "Symbolizes inspiration and new beginnings, igniting passion and creativity."),
    # ("2 of Wands", "Denotes planning and progress, encouraging you to expand your horizons."),
    # ("3 of Wands", "Represents foresight and expansion, highlighting opportunities for growth."),
    # ("4 of Wands", "Embodies celebration and harmony, marking milestones and joyful occasions."),
    # ("5 of Wands", "Signifies competition and conflict, reminding you to navigate challenges wisely."),
    # ("6 of Wands", "Denotes victory and recognition, celebrating achievements and public acclaim."),
    # ("7 of Wands", "Represents defense and perseverance, encouraging you to stand your ground."),
    # ("8 of Wands", "Symbolizes speed and action, indicating swift progress and movement."),
    # ("9 of Wands", "Denotes resilience and persistence, highlighting your strength to overcome obstacles."),
    # ("10 of Wands", "Embodies burden and responsibility, advising you to delegate tasks and seek support.")
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
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    first_name = update.message.from_user.first_name
    last_name = update.message.from_user.last_name
    add_user_to_db(user_id, username, first_name, last_name)

    card = random.choice(tarot_cards)
    caption = f"**{card['name']}**\n\n*Meaning:* {card['meaning']}\n*Example:* {card['example']}"
    try:
        with open(card['image_path'], 'rb') as image_file:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_file, caption=caption, parse_mode='Markdown')
    except FileNotFoundError:
        await update.message.reply_text(f"Image for {card['name']} not found. Please check the image path.")

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
