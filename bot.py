import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# List of Tarot cards and their meanings
tarot_cards = [
    ("The Fool", "New beginnings, optimism, trust in life"),
    ("The Magician", "Action, the power to manifest"),
    ("The High Priestess", "Inaction, going within, the mystical"),
    ("The Empress", "Abundance, nurturing, fertility, life in bloom!"),
    ("The Emperor", "Structure, stability, rules, and power"),
    ("The Hierophant", "Institutions, tradition, society, and its rules"),
    ("The Lovers", "Sexuality, passion, choice, uniting"),
    ("The Chariot", "Movement, progress, integration"),
    ("Strength", "Courage, determination, inner strength"),
    ("The Hermit", "Soul-searching, introspection, being alone"),
    ("Wheel of Fortune", "Luck, karma, life cycles"),
    ("Justice", "Fairness, truth, law"),
    ("The Hanged Man", "Pause, suspension, letting go"),
    ("Death", "Endings, transformation, transition"),
    ("Temperance", "Balance, moderation, purpose"),
    ("The Devil", "Addiction, materialism, playfulness"),
    ("The Tower", "Sudden upheaval, broken pride, disaster"),
    ("The Star", "Hope, faith, purpose, renewal"),
    ("The Moon", "Illusion, fear, anxiety, subconscious"),
    ("The Sun", "Success, vitality, joy"),
    ("Judgement", "Judgement, rebirth, inner calling"),
    ("The World", "Completion, celebration, accomplishment"),
    ("Ace of Cups", "New feelings, spirituality, intuition"),
    ("2 of Cups", "Unified love, partnership, mutual attraction"),
    ("3 of Cups", "Celebration, friendship, creativity"),
    ("4 of Cups", "Meditation, contemplation, apathy"),
    ("5 of Cups", "Regret, failure, disappointment"),
    ("6 of Cups", "Nostalgia, reunion, childhood memories"),
    ("7 of Cups", "Opportunities, choices, wishful thinking"),
    ("8 of Cups", "Disappointment, abandonment, withdrawal"),
    ("9 of Cups", "Contentment, satisfaction, gratitude"),
    ("10 of Cups", "Happiness, emotional fulfillment, alignment"),
    ("Ace of Pentacles", "Prosperity, new ventures, opportunity"),
    ("2 of Pentacles", "Balance, adaptability, time management"),
    ("3 of Pentacles", "Teamwork, collaboration, building"),
    ("4 of Pentacles", "Conservation, security, frugality"),
    ("5 of Pentacles", "Isolation, insecurity, worry"),
    ("6 of Pentacles", "Generosity, charity, giving"),
    ("7 of Pentacles", "Long-term view, sustainable results"),
    ("8 of Pentacles", "Education, apprenticeship, mastery"),
    ("9 of Pentacles", "Gratitude, luxury, self-sufficiency"),
    ("10 of Pentacles", "Legacy, inheritance, family"),
    ("Ace of Swords", "New ideas, mental clarity, breakthrough"),
    ("2 of Swords", "Difficult choices, indecision, stalemate"),
    ("3 of Swords", "Heartbreak, emotional pain, sorrow"),
    ("4 of Swords", "Rest, recovery, contemplation"),
    ("5 of Swords", "Conflict, tension, defeat"),
    ("6 of Swords", "Transition, rite of passage, moving on"),
    ("7 of Swords", "Betrayal, deception, stealth"),
    ("8 of Swords", "Restriction, limitation, negative thoughts"),
    ("9 of Swords", "Anxiety, worry, fear"),
    ("10 of Swords", "Betrayal, backstabbing, rock bottom"),
    ("Ace of Wands", "Inspiration, new beginnings, creativity"),
    ("2 of Wands", "Future planning, progress, decisions"),
    ("3 of Wands", "Expansion, foresight, overseas opportunities"),
    ("4 of Wands", "Celebration, harmony, home"),
    ("5 of Wands", "Conflict, competition, tension"),
    ("6 of Wands", "Victory, success, recognition"),
    ("7 of Wands", "Challenge, competition, protection"),
    ("8 of Wands", "Speed, action, swift change"),
    ("9 of Wands", "Courage, persistence, resilience"),
    ("10 of Wands", "Burden, responsibility, hard work")
]

# Command to start the bot
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Hello! I am your Tarot bot.')

# Command to fetch a random Tarot card
async def tarot(update: Update, context: CallbackContext) -> None:
    card = random.choice(tarot_cards)
    name, meaning = card
    await update.message.reply_text(f"Today's card: {name}\nMeaning: {meaning}")

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
