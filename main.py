import os
import logging
import re # New Import for Room Number Validation
import asyncio
from dotenv import load_dotenv
from telegram import ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler
)

# Import all required constants from the unified constants module
from merged_constants import (
    SELECT_HOSTEL,
    GET_ROOM_NUMBER,
    SELECT_CATEGORY,
    GET_DESCRIPTION,
    SUBMIT_COMPLAINT,
    HOSTELS,
    CATEGORY_LABELS,
    CATEGORY_LABEL_TO_KEY,
)

# Client for backend interactions (mock/stub)
from client import submit_complaint as client_submit
from client import get_complaint_status as client_get_status
from merged_constants import STATUS_KEY_TO_LABEL

# Local state for the status-check conversation
STATUS_WAITING_FOR_ID = 100

# Backwards-compatible variable name expected by existing code
COMPLAINT_CATEGORIES = CATEGORY_LABELS

# --- Configuration and Setup ---

# Load environment variables from .env file
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in .env file. Ensure it is set and the file is named '.env'.")

# Set up logging for the application
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# --- Command Handlers (Basic) ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
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
    """Handles the /help command."""
    help_message = (
        "**Available Commands:**\n"
        "🔹 **/report** - Start a new conversation to log a maintenance complaint.\n"
        "🔹 **/status** - (Phase 2: Coming Soon) Check the current status of a submitted ticket.\n"
        "🔹 **/help** - Show this list of commands.\n\n"
        "To submit a request, just type **/report**!"
    )
    await update.message.reply_html(help_message)


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles unknown commands."""
    await update.message.reply_text(
        "Sorry, I didn't recognize that command. "
        "Please use /report to log a complaint or /help to see available commands."
    )


# --- Conversation Handlers (Task C.2 & C.3 Implementation) ---

async def report_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry point for the conversation. Prompts for the Hostel choice (State: SELECT_HOSTEL).
    """
    # Build the inline keyboard dynamically from the HOSTELS list
    keyboard = []
    for i in range(0, len(HOSTELS), 2):
        row = []
        row.append(InlineKeyboardButton(HOSTELS[i], callback_data=f"hostel_{HOSTELS[i]}"))
        if i + 1 < len(HOSTELS):
            row.append(InlineKeyboardButton(HOSTELS[i+1], callback_data=f"hostel_{HOSTELS[i+1]}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❌ Cancel Report", callback_data='cancel')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Initialize the temporary complaint data
    context.user_data['complaint'] = {} 
    context.user_data['complaint']['telegram_user_id'] = update.effective_user.id
    
    await update.message.reply_text(
        "**REPORTING SYSTEM: 1 of 4**\n\nPlease select the hostel where the issue is located:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return SELECT_HOSTEL


async def select_hostel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles hostel selection (State: SELECT_HOSTEL -> GET_ROOM_NUMBER).
    """
    query = update.callback_query
    await query.answer()
    
    # Extract selected hostel from callback_data
    hostel_name = query.data.split('_')[1]
    
    # Store the data
    context.user_data['complaint']['hostel'] = hostel_name
    
    logger.info(f"User {query.from_user.id} selected hostel: {hostel_name}")

    # Prompt for the next step: Room Number
    await query.edit_message_text(
        f"Hostel selected: **{hostel_name}**\n\n"
        "**REPORTING SYSTEM: 2 of 4**\n\nPlease enter the **Room Number** (e.g., B201, 305):",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel Report", callback_data='cancel')]])
    )
    
    return GET_ROOM_NUMBER


async def get_room_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles and validates room number input (State: GET_ROOM_NUMBER -> SELECT_CATEGORY).
    """
    room_input = update.message.text.strip()
    
    # 1. Validation Logic: Checks for basic alphanumeric format and length
    if not (3 <= len(room_input) <= 5 and re.match(r'^[A-Za-z0-9]+$', room_input)):
        await update.message.reply_text(
            "⚠️ **Invalid Room Number Format.**\n"
            "Please enter a valid room number (e.g., A101, B205, 302). It should be 3-5 alphanumeric characters.",
            parse_mode='Markdown'
        )
        # Reprompt for the same state
        return GET_ROOM_NUMBER

    # Store the data
    context.user_data['complaint']['room_number'] = room_input
    logger.info(f"Room number stored: {room_input}")

    # Build the inline keyboard for the next step: Category Selection
    keyboard = []
    for i in range(0, len(COMPLAINT_CATEGORIES), 1): # One button per row for readability
        category = COMPLAINT_CATEGORIES[i]
        keyboard.append([InlineKeyboardButton(category, callback_data=f"category_{category}")])

    keyboard.append([InlineKeyboardButton("❌ Cancel Report", callback_data='cancel')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Room number confirmed: **{room_input}**\n\n"
        "**REPORTING SYSTEM: 3 of 4**\n\nPlease select the **Type of Issue**:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return SELECT_CATEGORY


async def select_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles category selection (State: SELECT_CATEGORY -> GET_DESCRIPTION).
    """
    query = update.callback_query
    await query.answer()

    # Extract selected category
    category_name = query.data.split('_', 1)[1] # Use split to handle spaces in category names
    
    # Store the data
    context.user_data['complaint']['category'] = category_name
    
    logger.info(f"User {query.from_user.id} selected category: {category_name}")

    # Prompt for the next step: Detailed Description
    await query.edit_message_text(
        f"Issue type selected: **{category_name}**\n\n"
        "**REPORTING SYSTEM: 4 of 4 (Final Step)**\n\n"
        "Please provide a **detailed description** of the problem.\n"
        "_Minimum 10 characters, Maximum 500 characters._",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel Report", callback_data='cancel')]])
    )
    
    return GET_DESCRIPTION


async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles and validates the detailed description (State: GET_DESCRIPTION -> SUBMIT_COMPLAINT).
    """
    description_input = update.message.text.strip()
    
    MIN_LEN = 10
    MAX_LEN = 500
    
    # 1. Validation Logic: Checks for length constraints
    if len(description_input) < MIN_LEN:
        await update.message.reply_text(
            f"⚠️ **Description is too short.**\n"
            f"Please describe the issue in more detail (minimum {MIN_LEN} characters).",
            parse_mode='Markdown'
        )
        return GET_DESCRIPTION
        
    if len(description_input) > MAX_LEN:
        await update.message.reply_text(
            f"⚠️ **Description is too long.**\n"
            f"Please shorten your description to under {MAX_LEN} characters.",
            parse_mode='Markdown'
        )
        return GET_DESCRIPTION

    # Store the data
    context.user_data['complaint']['description'] = description_input
    
    # Proceed to the final submission state (logic placeholder for D.2)
    return await submit_complaint_and_end(update, context) 


async def submit_complaint_and_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Placeholder for the final submission logic. (Task D.2 will implement the mock API call here).
    """
    final_data = context.user_data.get('complaint', {})
    logger.info(f"*** FINAL DATA COLLECTED (Submission): {final_data} ***")

    # Build payload expected by the backend/schema
    payload = {
        "telegram_user_id": str(final_data.get('telegram_user_id', '')),
        "hostel": final_data.get('hostel'),
        "room_number": final_data.get('room_number'),
        # Convert display label to storage key when possible
        "category": CATEGORY_LABEL_TO_KEY.get(final_data.get('category'), final_data.get('category')),
        "description": final_data.get('description'),
        # Use a default severity for now if not provided
        "severity": final_data.get('severity', 'medium'),
    }

    # Call the synchronous client stub in a thread to avoid blocking the event loop
    try:
        response = await asyncio.to_thread(client_submit, payload)
    except Exception as exc:
        logger.exception("Error when calling client.submit_complaint: %s", exc)
        await update.message.reply_text(
            "⚠️ There was an error submitting your complaint. Please try again later."
        )
        return ConversationHandler.END

    # Handle mock/real response
    complaint_id = None
    if isinstance(response, dict):
        complaint_id = response.get("complaint_id") or response.get("id")

    if complaint_id:
        await update.message.reply_text(
            "✅ Your complaint has been submitted successfully!\n\n"
            f"Complaint ID: `{complaint_id}`\n"
            "We will notify you when the status changes. Thank you!",
            parse_mode='Markdown'
        )
    else:
        # Fallback message if backend returned an unexpected response
        await update.message.reply_text(
            "✅ Data collected but the backend did not return an ID.\n"
            "Your complaint has been saved locally for now. Please try again later to get an official ID."
        )

    # Clear data and end conversation
    if 'complaint' in context.user_data:
        del context.user_data['complaint']

    return ConversationHandler.END


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Allows the user to cancel the conversation at any point using /cancel or the inline button.
    """
    user = update.effective_user
    logger.info(f"User {user.id} cancelled the conversation.")
    
    if 'complaint' in context.user_data:
        del context.user_data['complaint']
        
    # Determine how to respond based on if it was a command or a callback query
    if update.callback_query:
        await update.callback_query.answer()
        # Use edit_message_text for callback queries to replace the prompt
        await update.callback_query.edit_message_text(
            "Complaint reporting cancelled. Start a new one with /report."
        )
    else:
        # Use reply_text for command handler (user typed /cancel)
        await update.message.reply_text(
            "Complaint reporting cancelled. Start a new one with /report.",
            reply_markup=ReplyKeyboardRemove()
        )
    
    return ConversationHandler.END


# --- Main Application Logic ---

def main():
    """Initializes and runs the bot application."""
    logger.info("Starting bot application...")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # --- Conversation Handler Definition ---
    complaint_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('report', report_entry)],

        # Define all states and the expected handlers for each
        states={
            SELECT_HOSTEL: [
                CallbackQueryHandler(select_hostel_callback, pattern=r'^hostel_.*')
            ],
            
            GET_ROOM_NUMBER: [
                # Expecting a text message, passing it to the validation function
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_room_number)
            ],
            
            SELECT_CATEGORY: [
                CallbackQueryHandler(select_category_callback, pattern=r'^category_.*')
            ],
            
            GET_DESCRIPTION: [
                # Expecting a text message for the detailed description
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)
            ],
            
            SUBMIT_COMPLAINT: [
                # This state is handled internally by get_description calling submit_complaint_and_end
                # No external handlers needed here.
            ]
        },

        # Fallbacks to exit the conversation cleanly
        fallbacks=[
            CommandHandler('cancel', cancel_handler),
            CallbackQueryHandler(cancel_handler, pattern='^cancel$'),
        ]
    )
    
    # --- Register Handlers ---
    application.add_handler(complaint_conversation_handler)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # --- Status check conversation: supports `/status <ID>` or `/status` then ID
    async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Entry for /status. If an ID is provided inline, fetch immediately; otherwise prompt."""
        # If user typed `/status <id>` handle inline
        text = update.message.text or ""
        parts = text.split(maxsplit=1)
        if len(parts) > 1 and parts[1].strip():
            complaint_id = parts[1].strip()
            await update.message.reply_text("⏳ Checking status...")
            try:
                resp = await asyncio.to_thread(client_get_status, complaint_id)
            except Exception as exc:
                logger.exception("Error fetching status for %s: %s", complaint_id, exc)
                await update.message.reply_text("⚠️ Could not fetch status. Please try again later.")
                return ConversationHandler.END

            status_key = resp.get("status") if isinstance(resp, dict) else None
            friendly = STATUS_KEY_TO_LABEL.get(status_key, status_key) if status_key else "Unknown"
            await update.message.reply_text(f"Status for `{complaint_id}`: *{friendly}*", parse_mode='Markdown')
            return ConversationHandler.END

        # No ID inline; prompt the user
        await update.message.reply_text("Please send the Complaint ID you want to check (or /cancel to abort):")
        return STATUS_WAITING_FOR_ID

    async def status_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handles the message containing complaint ID and replies with status."""
        complaint_id = (update.message.text or "").strip()
        if not complaint_id:
            await update.message.reply_text("Please provide a non-empty Complaint ID or /cancel to abort.")
            return STATUS_WAITING_FOR_ID

        await update.message.reply_text("⏳ Checking status...")
        try:
            resp = await asyncio.to_thread(client_get_status, complaint_id)
        except Exception as exc:
            logger.exception("Error fetching status for %s: %s", complaint_id, exc)
            await update.message.reply_text("⚠️ Could not fetch status. Please try again later.")
            return ConversationHandler.END

        status_key = resp.get("status") if isinstance(resp, dict) else None
        friendly = STATUS_KEY_TO_LABEL.get(status_key, status_key) if status_key else "Unknown"
        await update.message.reply_text(f"Status for `{complaint_id}`: *{friendly}*", parse_mode='Markdown')
        return ConversationHandler.END

    status_conversation = ConversationHandler(
        entry_points=[CommandHandler('status', status_command)],
        states={
            STATUS_WAITING_FOR_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, status_id_handler)]
        },
        fallbacks=[CommandHandler('cancel', cancel_handler)],
    )

    application.add_handler(status_conversation)

    logger.info("Bot is initialized. Polling for updates...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    logger.info("Bot application stopped.")


if __name__ == '__main__':
    main()
