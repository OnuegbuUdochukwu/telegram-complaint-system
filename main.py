import os
import logging
from dotenv import load_dotenv
from telegram import ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler, # New Import
    CallbackQueryHandler # New Import
)

# Import the constants file we created in Task C.1
from constants import SELECT_HOSTEL, GET_ROOM_NUMBER, COMPLAINT_CATEGORIES, HOSTELS

# --- Configuration and Setup ---

# Load environment variables from .env file
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    # Use a more descriptive error for better debugging
    raise ValueError("TELEGRAM_BOT_TOKEN not found in .env file. Ensure it is set and the file is named '.env'.")

# Set up logging for the application
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# --- Command Handlers (Basic) ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles unknown commands (friendly redirection).
    """
    await update.message.reply_text(
        "Sorry, I didn't recognize that command. "
        "Please use /report to log a complaint or /help to see available commands."
    )


# --- Conversation Handlers (Core of Task C.2) ---

async def report_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry point for the conversation. Prompts the user to select their hostel.
    This function corresponds to the transition to SELECT_HOSTEL state (1).
    """
    # Build the inline keyboard dynamically from the HOSTELS list in constants.py
    keyboard = []
    # Create buttons in pairs for a cleaner layout
    for i in range(0, len(HOSTELS), 2):
        row = []
        row.append(InlineKeyboardButton(HOSTELS[i], callback_data=f"hostel_{HOSTELS[i]}"))
        if i + 1 < len(HOSTELS):
            row.append(InlineKeyboardButton(HOSTELS[i+1], callback_data=f"hostel_{HOSTELS[i+1]}"))
        keyboard.append(row)
    
    # Add a cancel button at the end
    keyboard.append([InlineKeyboardButton("Cancel Report", callback_data='cancel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Store a temporary dictionary to hold complaint data during the conversation
    context.user_data['complaint'] = {} 
    
    await update.message.reply_text(
        "**REPORTING SYSTEM: STEP 1 of 4**\n\nPlease select the hostel where the issue is located:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    # Return the next state ID defined in constants.py
    return SELECT_HOSTEL


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Allows the user to cancel the conversation at any point using /cancel or the inline button.
    """
    user = update.effective_user
    logger.info(f"User {user.id} cancelled the conversation.")
    
    # Clear any temporary data stored for the conversation
    if 'complaint' in context.user_data:
        del context.user_data['complaint']
        
    # Send confirmation message and remove the keyboard if it was present
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Complaint reporting cancelled. You can start a new one anytime with /report.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # End the conversation flow
    return ConversationHandler.END

async def dummy_state_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Placeholder handler for the next state (GET_ROOM_NUMBER) in the flow. 
    Task C.3 will replace this with real logic.
    """
    # This handler is only active if the user successfully selected a hostel (Task C.3)
    # For now, it just shows what the next state should be
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"DEBUG: Hostel Selected. Proceeding to state {GET_ROOM_NUMBER} (Room Number Input)."
    )
    
    # Since we are just structuring, we end the conversation here for C.2, 
    # but in C.3 we will return the actual next state ID.
    return ConversationHandler.END


# --- Main Application Logic ---

def main():
    """
    Initializes and runs the bot application, setting up all command and conversation handlers.
    """
    logger.info("Starting bot application...")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # --- Conversation Handler Definition ---
    complaint_conversation_handler = ConversationHandler(
        # Entry point: The /report command starts the conversation
        entry_points=[CommandHandler('report', report_entry)],

        # States: Define the structure of the multi-step form
        states={
            # State 1: Expecting a callback query (button click) after hostel selection
            SELECT_HOSTEL: [
                CallbackQueryHandler(dummy_state_handler, pattern=r'^hostel_.*')
            ],
            # Other states will be added in Task C.3 (GET_ROOM_NUMBER, SELECT_CATEGORY, etc.)
        },

        # Fallbacks: Actions to take if the user deviates from the expected flow
        fallbacks=[
            # 1. Handle /cancel command typed by the user
            CommandHandler('cancel', cancel_handler), 
            # 2. Handle 'cancel' button clicked by the user (sent as a callback query)
            CallbackQueryHandler(cancel_handler, pattern='^cancel$'), 
        ]
    )
    
    # --- Register Handlers ---
    
    # 1. Register Conversation Handler (Highest priority)
    application.add_handler(complaint_conversation_handler)

    # 2. Register Basic Command Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    # 3. Generic Message Handler (Lowest priority - MUST be added last)
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    logger.info("Bot is initialized. Polling for updates...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    logger.info("Bot application stopped.")


if __name__ == '__main__':
    main()
