import os
import logging
import re  # New Import for Room Number Validation
import asyncio
from dotenv import load_dotenv
from telegram import (
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.request import HTTPXRequest
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)

# Import all required constants from the unified constants module
from merged_constants import (
    GET_TELEGRAM_ID,
    SELECT_HOSTEL,
    GET_ROOM_NUMBER,
    SELECT_CATEGORY,
    GET_DESCRIPTION,
    SELECT_SEVERITY,
    SUBMIT_COMPLAINT,
    HOSTELS,
    CATEGORY_LABELS,
    CATEGORY_LABEL_TO_KEY,
    SEVERITY_KEYS,
    SEVERITY_LABELS,
    TELEGRAM_USER_ID_PATTERN,
    ROOM_NUMBER_PATTERN,
)

# Compile a module-level regex for known commands so the unknown handler
# can double-check and avoid replying when a valid command was sent.
KNOWN_COMMANDS_RE = re.compile(
    r"^/(?:start|report|status|mycomplaints|help|cancel|skip|done)(?:@[^\s@/]+)?\b",
    re.IGNORECASE,
)

# Client for backend interactions (mock/stub)
# Ensure .env is loaded before importing `client` so BACKEND_URL and other
# env vars are available when `client` reads them at import time.
load_dotenv()

# Import the client after loading .env
from client import (
    submit_complaint as client_submit,
    get_complaint_status as client_get_status,
    upload_photo as client_upload_photo,
)
from merged_constants import STATUS_KEY_TO_LABEL

# Local state for the status-check conversation
STATUS_WAITING_FOR_ID = 100

# New state for attaching photos after submission
ATTACH_PHOTOS = 200

# Backwards-compatible variable name expected by existing code
COMPLAINT_CATEGORIES = CATEGORY_LABELS

# --- Configuration and Setup ---

# Environment variables are loaded above before importing the client
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Optional: point the bot to the backend API (when set the client will call the real API)
BACKEND_URL = os.getenv("BACKEND_URL")
# Optional service token the bot can use to authenticate to the backend when uploading photos
BACKEND_SERVICE_TOKEN = os.getenv("BACKEND_SERVICE_TOKEN")

if not TELEGRAM_BOT_TOKEN and not os.getenv("CI"):
    raise ValueError(
        "TELEGRAM_BOT_TOKEN not found in .env file. Ensure it is set and the file is named '.env'."
    )

# Set up logging for the application
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Log backend configuration so operators know whether the bot will use the real API
if BACKEND_URL:
    logger.info("Bot configured to use backend at %s", BACKEND_URL)
else:
    logger.info(
        "No BACKEND_URL configured — bot will use mock/fallback responses from client.py"
    )

if BACKEND_SERVICE_TOKEN:
    logger.info(
        "BACKEND_SERVICE_TOKEN is set — bot will attempt service-authenticated uploads to the backend"
    )
else:
    logger.info(
        "No BACKEND_SERVICE_TOKEN configured — uploads will rely on interactive auth or fall back as configured"
    )


async def safe_reply_to_update(update: Update | object, text: str, **kwargs) -> None:
    """Attempt to reply to the user in a resilient way. Swallows network/send errors.

    Uses Update.effective_message.reply_text when available.
    """
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(text, **kwargs)
        else:
            logger.debug(
                "safe_reply_to_update: no effective_message available on update; skipping reply"
            )
    except Exception:
        logger.warning("safe_reply_to_update: failed to send message to user")


async def safe_edit_callback_query(query, text: str, **kwargs) -> None:
    """Attempt to answer and edit a callback query; if that fails try replying to the chat.

    This helps when network errors occur during edit_message_text.
    """
    try:
        await query.answer()
        await query.edit_message_text(text, **kwargs)
    except Exception:
        logger.warning(
            "safe_edit_callback_query: failed to edit callback message; attempting to reply to chat"
        )
        try:
            if query.message:
                await query.message.reply_text(text, **kwargs)
        except Exception:
            logger.warning("safe_edit_callback_query: also failed to reply to chat")


# --- Command Handlers (Basic) ---


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    user = update.effective_user
    welcome_message = (
        f"Welcome, {user.mention_html()}! 👋\n\n"
        "I am the **Covenant University Hostel Complaint System Bot**, designed to digitize maintenance requests.\n\n"
        "Here's what I can do:\n"
        "🔹 **/report** - Submit a new maintenance request\n"
        "🔹 **/status** - Check the status of your complaints\n"
        "🔹 **/mycomplaints** - View all your submitted complaints\n"
        "🔹 **/help** - Show available commands\n\n"
        "**Status Lifecycle:**\n"
        "📝 Reported → 🔧 In Progress → ✅ Resolved\n"
        "⏸️ On Hold for reviews, ❌ Rejected if inapplicable\n\n"
        "Get started by typing **/report** or **/status** to track your requests!"
    )
    await update.message.reply_html(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /help command."""
    help_message = (
        "**Available Commands:**\n"
        "🔹 **/report** - Start a new conversation to log a maintenance complaint.\n"
        "🔹 **/status** - Check the status of your complaints.\n"
        "🔹 **/mycomplaints** - View all your submitted complaints.\n"
        "🔹 **/help** - Show this list of commands.\n\n"
        "To submit a request, just type **/report**!"
    )
    await update.message.reply_html(help_message)


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles unknown commands."""
    # Log the unknown command for debugging (helps diagnose why commands are missed)
    try:
        logger.info(
            "unknown_command invoked. update_type=%s message=%s callback_data=%s",
            type(update).__name__,
            getattr(update, "message", None) and getattr(update.message, "text", None),
            getattr(update, "callback_query", None)
            and getattr(update.callback_query, "data", None),
        )
    except Exception:
        logger.exception("Failed to log unknown command details")

    # If the text matches one of our known commands (may include @botname),
    # do nothing — the specific CommandHandler already handled it. This
    # prevents the fallback from replying after a valid command runs.
    try:
        msg_text = getattr(update, "message", None) and getattr(
            update.message, "text", None
        )
        if msg_text and KNOWN_COMMANDS_RE.match(msg_text):
            logger.debug(
                "unknown_command: received known command '%s' — skipping fallback reply",
                msg_text,
            )
            return
    except Exception:
        logger.debug(
            "unknown_command: failed to evaluate message text for known-command check"
        )

    # Friendly guidance to the user for truly unknown commands
    if getattr(update, "message", None):
        await update.message.reply_text(
            "Sorry, I didn't recognize that command. "
            "Please use /report to log a complaint or /help to see available commands."
        )
    else:
        # If there's no message (e.g. callback), try a safe reply path
        await safe_reply_to_update(
            update,
            "Sorry, I didn't recognize that command. Please use /report or /help.",
        )


# --- Conversation Handlers (Task C.2 & C.3 Implementation) ---


async def report_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry point for the conversation. Prompts for the Hostel choice (State: SELECT_HOSTEL).
    """
    # Initialize the temporary complaint data without any pre-filled values
    # Per requirement: do not populate telegram_user_id or any other field automatically.
    # Initialize complaint data and auto-capture the Telegram user id from the incoming update
    # (use effective_user.id to avoid manual-entry mismatches)
    context.user_data["complaint"] = {}
    try:
        context.user_data["complaint"]["telegram_user_id"] = str(
            update.effective_user.id
        )
    except Exception:
        # Fallback: if effective_user is not available for some reason, leave blank
        context.user_data["complaint"]["telegram_user_id"] = None

    # Prompt the user to select their hostel next (we skip manual Telegram id entry)
    keyboard = []
    for i in range(0, len(HOSTELS), 2):
        row = []
        row.append(
            InlineKeyboardButton(HOSTELS[i], callback_data=f"hostel_{HOSTELS[i]}")
        )
        if i + 1 < len(HOSTELS):
            row.append(
                InlineKeyboardButton(
                    HOSTELS[i + 1], callback_data=f"hostel_{HOSTELS[i+1]}"
                )
            )
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ Cancel Report", callback_data="cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "**REPORTING SYSTEM: 1 of 6**\n\nPlease select the hostel where the issue is located:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )

    return SELECT_HOSTEL


async def get_telegram_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Validate and store the Telegram user id provided by the user, then prompt for hostel selection.
    """
    text = (update.message.text or "").strip()
    if not TELEGRAM_USER_ID_PATTERN.match(text):
        await update.message.reply_text(
            "⚠️ Invalid Telegram user id format. Please enter the numeric id shown in your Telegram profile (digits only)."
        )
        return GET_TELEGRAM_ID

    context.user_data["complaint"]["telegram_user_id"] = text

    # Build and show hostel keyboard after collecting telegram id
    keyboard = []
    for i in range(0, len(HOSTELS), 2):
        row = []
        row.append(
            InlineKeyboardButton(HOSTELS[i], callback_data=f"hostel_{HOSTELS[i]}")
        )
        if i + 1 < len(HOSTELS):
            row.append(
                InlineKeyboardButton(
                    HOSTELS[i + 1], callback_data=f"hostel_{HOSTELS[i+1]}"
                )
            )
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ Cancel Report", callback_data="cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "**REPORTING SYSTEM: 1 of 6**\n\nPlease select the hostel where the issue is located:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )

    return SELECT_HOSTEL


async def select_hostel_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Handles hostel selection (State: SELECT_HOSTEL -> GET_ROOM_NUMBER).
    """
    query = update.callback_query
    await query.answer()

    # Extract selected hostel from callback_data
    hostel_name = query.data.split("_")[1]

    # Store the data
    context.user_data["complaint"]["hostel"] = hostel_name

    logger.info(f"User {query.from_user.id} selected hostel: {hostel_name}")

    # Prompt for the next step: Wing (explicit user input)
    await query.edit_message_text(
        f"Hostel selected: **{hostel_name}**\n\n"
        "**REPORTING SYSTEM: 2 of 6**\n\nPlease enter the **Room Number** (e.g., A312, B201, 305):",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Cancel Report", callback_data="cancel")]]
        ),
    )

    return GET_ROOM_NUMBER


async def get_room_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles and validates room number input (State: GET_ROOM_NUMBER -> SELECT_CATEGORY).
    """
    # Normalize: uppercase letters so inputs like 'a101' become 'A101'
    raw_input = (update.message.text or "").strip()
    room_input = raw_input.upper()

    # Strict validation: one letter A-H followed by three digits (e.g., A312)
    if not ROOM_NUMBER_PATTERN.match(room_input):
        await update.message.reply_text(
            "⚠️ Room number must be one letter (A–H) followed by three digits, like A312. "
            "Please enter a valid room number.",
            parse_mode="Markdown",
        )
        return GET_ROOM_NUMBER

    # Store the normalized value and derive the wing (first letter)
    context.user_data["complaint"]["room_number"] = room_input
    derived_wing = room_input[0] if len(room_input) >= 1 else "N/A"
    context.user_data["complaint"]["wing"] = derived_wing
    logger.info(f"Room number stored: {room_input}; derived wing: {derived_wing}")

    # Build the inline keyboard for the next step: Category Selection
    keyboard = []
    for i in range(
        0, len(COMPLAINT_CATEGORIES), 1
    ):  # One button per row for readability
        category = COMPLAINT_CATEGORIES[i]
        keyboard.append(
            [InlineKeyboardButton(category, callback_data=f"category_{category}")]
        )

    keyboard.append([InlineKeyboardButton("❌ Cancel Report", callback_data="cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Room number confirmed: **{room_input}**\n\n"
        "**REPORTING SYSTEM: 3 of 6**\n\nPlease select the **Type of Issue**:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )

    return SELECT_CATEGORY


async def select_category_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Handles category selection (State: SELECT_CATEGORY -> GET_DESCRIPTION).
    """
    query = update.callback_query
    await query.answer()

    # Extract selected category
    category_name = query.data.split("_", 1)[
        1
    ]  # Use split to handle spaces in category names

    # Store the data
    context.user_data["complaint"]["category"] = category_name

    logger.info(f"User {query.from_user.id} selected category: {category_name}")

    # Prompt for the next step: Detailed Description
    await query.edit_message_text(
        f"Issue type selected: **{category_name}**\n\n"
        "**REPORTING SYSTEM: 5 of 6**\n\n"
        "Please provide a **detailed description** of the problem.\n"
        "_Minimum 10 characters, Maximum 500 characters._",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Cancel Report", callback_data="cancel")]]
        ),
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
            parse_mode="Markdown",
        )
        return GET_DESCRIPTION

    if len(description_input) > MAX_LEN:
        await update.message.reply_text(
            f"⚠️ **Description is too long.**\n"
            f"Please shorten your description to under {MAX_LEN} characters.",
            parse_mode="Markdown",
        )
        return GET_DESCRIPTION

    # Store the data
    context.user_data["complaint"]["description"] = description_input

    # Prompt the user to select severity explicitly
    keyboard = []
    for i, key in enumerate(SEVERITY_KEYS):
        label = SEVERITY_LABELS[i] if i < len(SEVERITY_LABELS) else key.title()
        keyboard.append([InlineKeyboardButton(label, callback_data=f"severity_{key}")])
    keyboard.append([InlineKeyboardButton("❌ Cancel Report", callback_data="cancel")])

    await update.message.reply_text(
        "**REPORTING SYSTEM: 6 of 6 (Final Step)**\n\nPlease select the severity of the issue:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

    return SELECT_SEVERITY


async def select_severity_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle severity selection and then submit the complaint."""
    query = update.callback_query
    await query.answer()

    severity_key = query.data.split("_", 1)[1]
    if severity_key not in SEVERITY_KEYS:
        await query.edit_message_text("⚠️ Invalid severity selection. Please try again.")
        return SELECT_SEVERITY

    context.user_data["complaint"]["severity"] = severity_key

    # Proceed to submit now that all fields have been collected from the user
    await query.edit_message_text("Severity recorded. Submitting your complaint...")
    return await submit_complaint_and_end(update, context)


async def submit_complaint_and_end(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Placeholder for the final submission logic. (Task D.2 will implement the mock API call here).
    """
    final_data = context.user_data.get("complaint", {})
    logger.info(f"*** FINAL DATA COLLECTED (Submission): {final_data} ***")

    # Build payload expected by the backend/schema
    # Validate that all required fields were provided by the user
    missing = [
        k
        for k in (
            "telegram_user_id",
            "hostel",
            "wing",
            "room_number",
            "category",
            "description",
            "severity",
        )
        if not final_data.get(k)
    ]
    if missing:
        await safe_reply_to_update(
            update,
            f"⚠️ Missing required fields: {', '.join(missing)}. Please restart the report with /report and provide the requested values.",
        )
        return ConversationHandler.END

    payload = {
        "telegram_user_id": str(final_data.get("telegram_user_id")),
        "hostel": final_data.get("hostel"),
        "wing": final_data.get("wing"),
        "room_number": final_data.get("room_number"),
        # Convert display label to storage key when possible
        "category": CATEGORY_LABEL_TO_KEY.get(
            final_data.get("category"), final_data.get("category")
        ),
        "description": final_data.get("description"),
        "severity": final_data.get("severity"),
    }

    # Call the asynchronous client stub directly
    try:
        response = await client_submit(payload)
    except Exception as exc:
        logger.exception("Error when calling client.submit_complaint: %s", exc)
        await safe_reply_to_update(
            update,
            "⚠️ There was an error submitting your complaint. Please try again later.",
        )
        return ConversationHandler.END

    # Handle mock/real response
    complaint_id = None
    if isinstance(response, dict):
        complaint_id = response.get("complaint_id") or response.get("id")

    if complaint_id:
        # Store the created complaint id in user_data so subsequent photo uploads attach correctly
        context.user_data["current_complaint_id"] = complaint_id

        await safe_reply_to_update(
            update,
            "✅ Your complaint has been submitted successfully!\n\n"
            f"Complaint ID: `{complaint_id}`\n"
            "Would you like to attach photos to this complaint? If yes, send the photos now.\n"
            "When finished, type /done. To skip attachments type /skip.",
            parse_mode="Markdown",
        )

        # Transition to ATTACH_PHOTOS state to accept incoming photos
        return ATTACH_PHOTOS
    else:
        # Fallback message if backend returned an unexpected response
        await safe_reply_to_update(
            update,
            "✅ Data collected but the backend did not return an ID.\n"
            "Your complaint has been saved locally for now. Please try again later to get an official ID.",
        )

        # Clear data and end conversation
        if "complaint" in context.user_data:
            del context.user_data["complaint"]

        return ConversationHandler.END


async def handle_photo_upload(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle incoming photo messages while in ATTACH_PHOTOS state.

    Downloads the largest size of the photo and uploads it to the backend using
    the `client.upload_photo` helper.
    """
    if "current_complaint_id" not in context.user_data:
        await safe_reply_to_update(
            update, "No complaint context found. Start a new report with /report."
        )
        return ConversationHandler.END

    complaint_id = context.user_data["current_complaint_id"]

    # Telegram sends photos in several sizes - take the largest
    photo_sizes = update.message.photo
    if not photo_sizes:
        await safe_reply_to_update(update, "Could not find photo data in the message.")
        return ATTACH_PHOTOS

    file_id = photo_sizes[-1].file_id
    try:
        file = await context.bot.get_file(file_id)
        data = await file.download_as_bytearray()
        # Construct a filename using complaint id and file id
        filename = f"{complaint_id}_{file_id}.jpg"

        # Call the client upload directly
        try:
            result = await client_upload_photo(complaint_id, bytes(data), filename)
            await safe_reply_to_update(
                update, f"Uploaded photo: {result.get('id') or result.get('file_url')}"
            )
        except Exception as exc:
            logger.exception("Failed to upload photo from bot: %s", exc)
            await safe_reply_to_update(
                update, "⚠️ Failed to upload photo to server. Please try again later."
            )

    except Exception as exc:
        logger.exception("Error downloading photo from Telegram: %s", exc)
        await safe_reply_to_update(
            update, "⚠️ Could not download the photo from Telegram."
        )

    # Stay in the same state to accept more photos until /done or /skip
    return ATTACH_PHOTOS


async def finish_photo_uploads(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Finish attachment flow and end the conversation."""
    if "current_complaint_id" in context.user_data:
        cid = context.user_data["current_complaint_id"]
        await safe_reply_to_update(
            update,
            f"✅ Finished attaching photos to complaint `{cid}`. Thank you!",
            parse_mode="Markdown",
        )
        # Clean up
        del context.user_data["current_complaint_id"]
    else:
        await safe_reply_to_update(
            update, "No active complaint context. Start with /report."
        )
    if "complaint" in context.user_data:
        del context.user_data["complaint"]
    return ConversationHandler.END


async def finish_without_photos(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Skip attaching photos and end the conversation."""
    if "current_complaint_id" in context.user_data:
        cid = context.user_data["current_complaint_id"]
        await safe_reply_to_update(
            update,
            f"No photos attached. Complaint `{cid}` is complete.",
            parse_mode="Markdown",
        )
        del context.user_data["current_complaint_id"]
    else:
        await safe_reply_to_update(
            update, "No active complaint context. Start with /report."
        )
    if "complaint" in context.user_data:
        del context.user_data["complaint"]
    return ConversationHandler.END


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Allows the user to cancel the conversation at any point using /cancel or the inline button.
    """
    user = update.effective_user
    logger.info(f"User {user.id} cancelled the conversation.")

    if "complaint" in context.user_data:
        del context.user_data["complaint"]

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
            reply_markup=ReplyKeyboardRemove(),
        )

    return ConversationHandler.END


# --- Main Application Logic ---


def main():
    """Initializes and runs the bot application."""
    logger.info("Starting bot application...")

    # Configure a custom HTTP request object with larger timeouts and a small
    # connection pool to reduce the chance of ConnectTimeout/TCP issues during
    # short network blips when talking to the Telegram API.
    request = HTTPXRequest(
        connection_pool_size=32,
        connect_timeout=20.0,
        read_timeout=30.0,
        pool_timeout=10.0,
    )

    # Use the same HTTPXRequest instance for getUpdates polling. The
    # Application expects a BaseRequest-like object, not a dict. Passing the
    # request object ensures polling uses the same configured timeouts/pool.
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .request(request)
        .get_updates_request(request)
        .build()
    )

    # --- Enhanced status check with better UX
    async def get_my_complaints(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get all complaints for the current user."""
        user_id = str(update.effective_user.id)

        await safe_reply_to_update(update, "⏳ Fetching your complaints...")

        try:
            # Call backend to get user's complaints
            from client import get_user_complaints

            complaints = await get_user_complaints(user_id)
        except Exception as exc:
            logger.exception("Error fetching complaints for user %s: %s", user_id, exc)
            await safe_reply_to_update(
                update, "⚠️ Could not fetch your complaints. Please try again later."
            )
            return

        if not complaints or len(complaints.get("items", [])) == 0:
            await safe_reply_to_update(
                update,
                "📋 You haven't submitted any complaints yet.\n\n"
                "Use /report to submit a new complaint.",
            )
            return

        # Format the complaints list
        message_parts = ["📋 **Your Complaints**\n"]

        items = complaints.get("items", [])
        for idx, complaint in enumerate(items[:10], 1):  # Show first 10
            complaint_id = complaint.get("id", "Unknown")
            status = complaint.get("status", "reported")
            status_emoji = {
                "reported": "📝",
                "in_progress": "🔧",
                "on_hold": "⏸️",
                "resolved": "✅",
                "closed": "✔️",
                "rejected": "❌",
            }.get(status, "📄")

            status_label = STATUS_KEY_TO_LABEL.get(status, status.title())
            hostel = complaint.get("hostel", "Unknown")
            category = complaint.get("category", "Unknown")
            created_at = complaint.get("created_at", "")

            message_parts.append(
                f"{idx}. {status_emoji} *{status_label}*\n"
                f"   ID: `{complaint_id[:8]}`\n"
                f"   Hostel: {hostel} | Category: {category[:20]}\n"
            )

        if len(items) > 10:
            message_parts.append(f"\n_...and {len(items) - 10} more_")

        await safe_reply_to_update(
            update, "\n".join(message_parts), parse_mode="Markdown"
        )

    # Status check command - shows all complaints with status in a nice format
    async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's complaints with status in a nice format."""
        await get_my_complaints(update, context)

    # --- Conversation Handler Definition ---
    complaint_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("report", report_entry)],
        # Define all states and the expected handlers for each
        states={
            GET_TELEGRAM_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_telegram_id)
            ],
            SELECT_HOSTEL: [
                CallbackQueryHandler(select_hostel_callback, pattern=r"^hostel_.*")
            ],
            # GET_WING removed: wing is now derived from room number input
            GET_ROOM_NUMBER: [
                # Expecting a text message, passing it to the validation function
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_room_number)
            ],
            SELECT_CATEGORY: [
                CallbackQueryHandler(select_category_callback, pattern=r"^category_.*")
            ],
            GET_DESCRIPTION: [
                # Expecting a text message for the detailed description
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)
            ],
            SELECT_SEVERITY: [
                CallbackQueryHandler(select_severity_callback, pattern=r"^severity_.*")
            ],
            ATTACH_PHOTOS: [
                MessageHandler(filters.PHOTO, handle_photo_upload),
                CommandHandler("done", finish_photo_uploads),
                CommandHandler("skip", finish_without_photos),
            ],
            SUBMIT_COMPLAINT: [
                # This state is handled internally by select_severity_callback calling submit_complaint_and_end
                # No external handlers needed here.
            ],
        },
        # Fallbacks to exit the conversation cleanly and allow global commands
        # to be used at *any point* during the conversation (e.g. /skip, /done,
        # /status, /mycomplaints). Adding them here ensures they will be
        # handled even when the ConversationHandler is active.
        fallbacks=[
            CommandHandler("cancel", cancel_handler),
            CallbackQueryHandler(cancel_handler, pattern="^cancel$"),
            # Allow skipping or finishing photo attachments from any state
            CommandHandler("skip", finish_without_photos),
            CommandHandler("done", finish_photo_uploads),
            # Allow users to check status or list complaints while mid-flow
            CommandHandler("status", status_command),
            CommandHandler("mycomplaints", get_my_complaints),
        ],
    )

    # --- Register Handlers ---
    application.add_handler(complaint_conversation_handler)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    # Also register a top-level /report command handler to ensure the
    # reporting flow can be started even if ConversationHandler entry
    # registration misses the update (some Telegram updates may not
    # include command entities reliably). This is a safe idempotent
    # registration — ConversationHandler will still manage the flow.
    application.add_handler(CommandHandler("report", report_entry))
    # NOTE: don't add a global unknown_command handler yet — add it after all
    # specific command handlers (status, mycomplaints) so it doesn't swallow
    # legitimate commands registered later.

    # --- Enhanced status check with better UX
    async def get_my_complaints(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get all complaints for the current user."""
        user_id = str(update.effective_user.id)

        await safe_reply_to_update(update, "⏳ Fetching your complaints...")

        try:
            # Call backend to get user's complaints
            from client import get_user_complaints

            complaints = await asyncio.to_thread(get_user_complaints, user_id)
        except Exception as exc:
            logger.exception("Error fetching complaints for user %s: %s", user_id, exc)
            await safe_reply_to_update(
                update, "⚠️ Could not fetch your complaints. Please try again later."
            )
            return

        if not complaints or len(complaints.get("items", [])) == 0:
            await safe_reply_to_update(
                update,
                "📋 You haven't submitted any complaints yet.\n\n"
                "Use /report to submit a new complaint.",
            )
            return

        # Format the complaints list
        message_parts = ["📋 **Your Complaints**\n"]

        items = complaints.get("items", [])
        for idx, complaint in enumerate(items[:10], 1):  # Show first 10
            complaint_id = complaint.get("id", "Unknown")
            status = complaint.get("status", "reported")
            status_emoji = {
                "reported": "📝",
                "in_progress": "🔧",
                "on_hold": "⏸️",
                "resolved": "✅",
                "closed": "✔️",
                "rejected": "❌",
            }.get(status, "📄")

            status_label = STATUS_KEY_TO_LABEL.get(status, status.title())
            hostel = complaint.get("hostel", "Unknown")
            category = complaint.get("category", "Unknown")
            created_at = complaint.get("created_at", "")

            message_parts.append(
                f"{idx}. {status_emoji} *{status_label}*\n"
                f"   ID: `{complaint_id[:8]}`\n"
                f"   Hostel: {hostel} | Category: {category[:20]}\n"
            )

        if len(items) > 10:
            message_parts.append(f"\n_...and {len(items) - 10} more_")

        await safe_reply_to_update(
            update, "\n".join(message_parts), parse_mode="Markdown"
        )

    # Status check command - shows all complaints with inline buttons
    async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's complaints with status in a nice format."""
        await get_my_complaints(update, context)

    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("mycomplaints", get_my_complaints))

    # Finally add a global unknown-command handler as a last-resort fallback.
    # Only trigger this fallback for commands that are not one of the
    # explicitly-registered commands. We exclude the bot username suffix
    # (e.g. /report@MyBot) so users addressing a specific bot still match.
    # This prevents valid commands (registered above) from being followed by
    # the fallback when both handlers run for the same update.
    known_cmds_pattern = (
        r"^/(?:start|report|status|mycomplaints|help|cancel|skip|done)(?:@[^\s@/]+)?\b"
    )
    known_cmds_re = re.compile(known_cmds_pattern, re.IGNORECASE)
    unknown_filter = filters.COMMAND & ~filters.Regex(known_cmds_re)
    application.add_handler(MessageHandler(unknown_filter, unknown_command), group=99)

    # Global error handler to catch unexpected exceptions in handlers and
    # prevent the application from crashing. We also attempt to notify the
    # user that something went wrong where possible.
    async def global_error_handler(
        update: object, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Log exceptions and notify the user with a friendly message when possible."""
        logger.exception("Unhandled exception in update: %s", context.error)

        try:
            # If we have an Update with a message, attempt a polite reply.
            if isinstance(update, Update) and update.effective_message:
                await update.effective_message.reply_text(
                    "⚠️ Oops — something went wrong while processing your request. "
                    "Please try again in a moment."
                )
        except Exception:
            # Swallow all exceptions here; we've already logged the original.
            logger.warning("Failed to send error notification to user.")

    application.add_error_handler(global_error_handler)

    logger.info("Bot is initialized. Polling for updates...")

    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as exc:
        # Log unexpected errors during the polling lifecycle
        logger.exception("Unexpected error while polling: %s", exc)
    finally:
        logger.info("Bot application stopped.")


if __name__ == "__main__":
    main()
