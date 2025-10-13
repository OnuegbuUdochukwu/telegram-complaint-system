import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler

# --- Configuration and Setup ---

# 1. Load environment variables from .env file
# This must be called first to load the TELEGRAM_BOT_TOKEN
load_dotenv()

# Get the token securely. If it's missing, the program will crash here, which is intended.
# We use os.getenv() which is safer than hardcoding the token.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in .env file. Please check Task B.1 steps.")

# Set up logging for the application
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# --- Command Handlers (Basic Test) ---

async def start_command(update, context):
    """
    Handles the /start command. A basic command to confirm the bot is working.
    """
    user = update.effective_user
    await update.message.reply_html(
        f"Hello, {user.mention_html()}! 👋\n\n"
        "I am the Covenant University Hostel Complaint System Bot. "
        "The connection is verified. Ready for Phase 1 development!"
    )


# --- Main Application Logic ---

def main():
    """
    Initializes and runs the bot application.
    """
    logger.info("Starting bot application...")

    # 2. Instantiate the Application using the securely loaded token
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add a simple command handler for testing
    application.add_handler(CommandHandler("start", start_command))

    logger.info("Bot is initialized. Polling for updates...")
    
    # Run the bot until the user presses Ctrl-C
    # For Task B.1, this step confirms the connection works.
    application.run_polling()
    
    logger.info("Bot application stopped.")


if __name__ == '__main__':
    main()
