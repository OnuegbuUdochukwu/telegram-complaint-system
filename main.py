import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters

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


# --- Command Handlers ---

async def start_command(update, context):
    """
    Handles the /start command, welcoming the user and explaining the bot's purpose.
    """
    user = update.effective_user
    welcome_message = (
        f"Welcome, {user.mention_html()}! 👋\n\n"
        "I am the **Covenant University Hostel Complaint System Bot**, designed to digitize maintenance requests.\n\n"
        "Here's what I can do:\n"
        "🔹 Use the **/report** command to submit a new maintenance request (e.g., plumbing, electrical, etc.).\n"
        "🔹 Use the **/help** command to see this guide again."
    )
    await update.message.reply_html(welcome_message)


async def help_command(update, context):
    """
    Handles the /help command by repeating the main instructions.
    """
    help_message = (
        "**Available Commands:**\n"
        "🔹 **/report** - Start a new conversation to log a maintenance complaint.\n"
        "🔹 **/status** - (Phase 2: Coming Soon) Check the current status of a submitted ticket.\n"
        "🔹 **/help** - Show this list of commands.\n\n"
        "To submit a request, just type **/report**!"
    )
    await update.message.reply_html(help_message)


async def unknown_command(update, context):
    """
    Handles unknown commands (friendly redirection). This is the fallback handler.
    Note: Must be registered last.
    """
    await update.message.reply_text(
        "Sorry, I didn't recognize that command. "
        "Please use /report to log a complaint or /help to see available commands."
    )


# --- Main Application Logic ---

def main():
    """
    Initializes and runs the bot application, setting up handlers for all basic commands.
    """
    logger.info("Starting bot application...")

    # 2. Instantiate the Application using the securely loaded token
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # --- Register Handlers ---
    # Command Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    # Generic Message Handler (MUST be added last)
    # This catches any message that starts with '/' but did not match a specific CommandHandler above.
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    logger.info("Bot is initialized. Polling for updates...")
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling()
    
    logger.info("Bot application stopped.")


if __name__ == '__main__':
    main()
