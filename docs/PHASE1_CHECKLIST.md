# Phase 1 Development Checklist

## 🧩 Task Set A: Data Modeling and Environment Setup

    - [x] A.1 Finalize Complaint Data Schema

        - [x] List required fields for a complaint record (e.g., id, telegram_user_id, hostel, wing, room_number, category, description, severity, status, created_at).
        - [x] Define exact data type and constraints for each field (nullability, unique, defaults, length, formats).
        - [x] Define permissible values for enumerated fields (Categories, Statuses, Severity levels).
        - [x] Produce finalized schema document (JSON or Markdown) for the core complaints table.
        - Purpose: Provide a precise blueprint that maps Telegram inputs to the PostgreSQL data model for Phase 2.
        - Tools/Technologies: Markdown or JSON, DB schema conventions (Postgres types), documentation.
        - Expected Output: A finalized, documented schema file (e.g., `complaints_schema.md` or `complaints_schema.json`).

-   [x] A.2 Local Python Environment Setup
    -   [x] Create project directory `complaint_bot_project` (or use current repo root as desired).
    -   [x] Initialize Python virtual environment: `python3 -m venv .venv`.
    -   [x] Activate venv and install core libs: `pip install python-telegram-bot requests python-dotenv`.
    -   [x] Generate `requirements.txt`: `pip freeze > requirements.txt`.
    -   Purpose: Establish an isolated, reproducible environment to develop and run the bot.
    -   Tools/Technologies: Python 3.x, venv, pip, VS Code (or preferred IDE).
    -   Expected Output: `.venv` with installed dependencies and a committed `requirements.txt`.

**Progress:** 2/2 tasks completed (100%)

---

## 🧩 Task Set B: Core Bot Framework and Authentication

-   [x] B.1 Telegram Bot Registration and Secure Token Management

    -   [x] Register bot with BotFather and obtain TELEGRAM_BOT_TOKEN.
    -   [x] Add `.env` file to project root containing `TELEGRAM_BOT_TOKEN=...` (ensure `.env` is in `.gitignore`).
    -   [x] Implement secure loading with `python-dotenv` (load at app startup).
    -   [x] Verify token is loaded and passed to the `Application`/`ApplicationBuilder` instance.
    -   Purpose: Acquire credentials and ensure secrets are not hardcoded in source control.
    -   Tools/Technologies: Telegram (BotFather), python-dotenv, python-telegram-bot.
    -   Expected Output: A small script that imports the token from env and successfully instantiates the bot client.

-   [x] B.2 Basic Command Implementation and Handlers
    -   [x] Create main application loop and instantiate `ApplicationBuilder`.
    -   [x] Implement `/start` handler with welcome text explaining bot purpose and `/report` usage.
    -   [x] Implement `/help` handler listing available commands and brief usage.
    -   [x] Add a generic message handler/fallback to catch unknown commands and guide user.
    -   Purpose: Provide users with entry points and command routing for the bot.
    -   Tools/Technologies: python-telegram-bot (ApplicationBuilder, CommandHandler, MessageHandler).
    -   Expected Output: A running bot that responds to `/start`, `/help`, and provides a friendly fallback message.

**Progress:** 2/2 tasks completed (100%)

---

## 🧩 Task Set C: Complaint Logging Conversation Flow

-   [x] C.1 Conversation Flow Mapping and State Definition

    -   [x] Map the full user journey starting at the `/report` command.
    -   [x] Define named state constants: e.g., `SELECT_HOSTEL`, `GET_ROOM_NUMBER`, `SELECT_CATEGORY`, `GET_DESCRIPTION`, `CONFIRM`.
    -   [x] Produce a diagram or textual flow that shows transitions and fallback/cancel behavior.
    -   Purpose: Define the state machine to guide implementation of the multi-step form.
    -   Tools/Technologies: Markdown, simple diagram tool (optional), Python constants module (e.g., `constants.py`).
    -   Expected Output: A states module plus a flow diagram or document describing transitions.

-   [x] C.2 Implement Conversation Handler Structure

    -   [x] Create a `ConversationHandler` instance wired to the defined state constants.
    -   [x] Implement `/report` entry handler that starts the conversation and prompts for Hostel (inline keyboard).
    -   [x] Implement fallback handler(s) including `/cancel` to abort and clear conversation state.
    -   [x] Attach the `ConversationHandler` to the main application dispatcher.

-   Purpose: Build the control structure for the multi-step complaint submission.
-   Tools/Technologies: python-telegram-bot (ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler).
-   Expected Output: Conversation handler that can be started and canceled cleanly.

-   [x] C.3 Input Validation and Inline Keyboard Integration
-   [x] Implement inline keyboards for Hostel and Category selection (use `InlineKeyboardMarkup` + callback handlers).
-   [x] Implement Room Number input step with validation (alphanumeric/format or numeric range); re-prompt on invalid input.
-   [x] Implement Description step with length validation (min 10 chars, max 500 chars); re-prompt on invalid input.
-   [x] Store all collected data temporarily in `context.user_data` (so `submit` can use it).
-   Purpose: Ensure data integrity and create a smooth, guided UX for users.
-   Tools/Technologies: python-telegram-bot, `InlineKeyboardMarkup`, `CallbackQueryHandler`, regex/string validation.
-   Expected Output: A conversation flow where choices are buttons, text inputs are validated, and data is collected in `context.user_data`.

**Progress:** 3/3 tasks completed (100%)

---

## 🧩 Task Set D: Mock Backend and Status Functionality

-   [x] D.1 Initial Backend API Stub Creation

    -   [x] Create `client.py` module for backend interactions.
    -   [x] Implement `submit_complaint(data)` stub that simulates a POST (using `requests`) and returns a mock success (e.g., `{ "status": "success", "complaint_id": "MOCK-12345" }`).
    -   [x] Implement `get_complaint_status(id)` stub returning a mock status (e.g., `{ "status": "Resolved" }`).
    -   Purpose: Decouple bot logic from the real backend by providing testable mock functions.
    -   Tools/Technologies: Python, `requests`.
    -   Expected Output: `client.py` with `submit_complaint` and `get_complaint_status` functions returning deterministic mock responses.

-   [x] D.2 Final Submission Integration (Mock)

    -   [x] In the final conversation state, build payload from `context.user_data`.
    -   [x] Call `submit_complaint()` stub and handle its response.
    -   [x] On success, clear `context.user_data` and send a confirmation message with mock ID (`Thank you! Your complaint has been logged with ID: [MOCK-ID].`).
    -   Purpose: Complete the end-to-end flow for reporting using the mock backend.
    -   Tools/Technologies: python-telegram-bot, `client.py` stub.
    -   Expected Output: End-to-end `/report` → mock submit → user confirmation flow.

-   [x] D.3 Implement Mock Status Check Command
    -   [x] Implement `/status` command handler to prompt user for Complaint ID.
    -   [x] Call `get_complaint_status(id)` and reply to the user with the returned mock status.
    -   [x] Handle invalid/nonexistent IDs gracefully (reply that no record was found or show usage).
    -   Purpose: Allow users to check the status of their submitted tickets while backend is being built.
    -   Tools/Technologies: python-telegram-bot, `client.py` stub.
    -   Expected Output: A working `/status` command that returns mock statuses for supplied IDs.

**Progress:** 3/3 tasks completed (100%)

---

## ⚙️ Overall Progress

**Total Tasks:** 10  
**Completed:** 10  
**Overall Progress:** 100%

---

### Next steps (optional)

-   Convert this checklist into a tracked issue or project board for granular tracking.
-   I can create the skeleton files (`constants.py`, `client.py`, `bot.py`) and/or run environment setup (A.2) if you want.
