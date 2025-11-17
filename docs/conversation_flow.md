# Complaint Reporting Conversation Flow

This document describes the multi-step `/report` conversation used by the Telegram bot. It lists the states, expected inputs, validation rules, transitions, data storage, and fallbacks.

## Overview

-   Entry: `/report` command.
-   Purpose: Guide a user through reporting a hostel maintenance complaint in a short, validated conversation and collect a complete complaint payload.
-   Temporary storage: `context.user_data['complaint']` (in-memory per user for the conversation lifetime).

## States and inputs

-   SELECT_HOSTEL (CallbackQuery)

    -   Prompt: Inline keyboard listing hostels.
    -   Input: Button press -> callback*data `hostel*<HOSTEL_NAME>`.
    -   On success: store `complaint['hostel']`, go to GET_ROOM_NUMBER.
    -   On cancel: callback `cancel` -> cancel_handler -> end.

-   GET_ROOM_NUMBER (Text)

    -   Prompt: Ask user to type room number (e.g., "A312", "B205", "302").
    -   Input: free text message.
    -   Validation: alphanumeric; length 3–5 characters (current implementation uses regex `^[A-Za-z0-9]+$` and length check).
    -   On valid: store `complaint['room_number']`, go to SELECT_CATEGORY.
    -   On invalid: re-prompt with guidance and remain in GET_ROOM_NUMBER.
    -   On cancel: `/cancel` command -> cancel_handler -> end.

-   SELECT_CATEGORY (CallbackQuery)

    -   Prompt: Inline keyboard listing complaint categories (one button per row for readability).
    -   Input: Button press -> callback*data `category*<CATEGORY_LABEL>`.
    -   On success: store `complaint['category']`, go to GET_DESCRIPTION.
    -   On cancel: callback `cancel` -> cancel_handler -> end.

-   GET_DESCRIPTION (Text)

    -   Prompt: Ask user to provide a detailed description (min 10 chars, max 500 chars).
    -   Input: free text message.
    -   Validation: length between 10 and 500 characters.
    -   On valid: store `complaint['description']` and proceed to submission state (SUBMIT_COMPLAINT).
    -   On invalid: re-prompt and remain in GET_DESCRIPTION.
    -   On cancel: `/cancel` command or cancel callback -> cancel_handler -> end.

-   SUBMIT_COMPLAINT (internal/terminal)
    -   Current Phase: placeholder that confirms collected data to the user and clears `context.user_data['complaint']`.
    -   Future Phase: call `client.submit_complaint(payload)` and handle API response, send confirmation with ID, or show error and retry guidance.

## Data stored in `context.user_data['complaint']`

-   telegram_user_id
-   hostel
-   room_number
-   category
-   description
-   (future) severity, status, photo_urls

Example payload (what will be built for submission):

```json
{
    "telegram_user_id": 123456789,
    "hostel": "A",
    "room_number": "A312",
    "category": "plumbing",
    "description": "Sink in the bathroom is leaking from the pipe under the basin.",
    "severity": "medium",
    "photo_urls": []
}
```

## Transitions (ASCII diagram)

Start (/report)
|
v
SELECT_HOSTEL --(button)--> GET_ROOM_NUMBER --(text/valid)--> SELECT_CATEGORY --(button)--> GET_DESCRIPTION --(text/valid)--> SUBMIT_COMPLAINT --> End

Cancel routes: at any step the inline "❌ Cancel Report" button or `/cancel` command routes to the `cancel_handler` which clears in-progress data and ends the conversation.

## Validation and UX notes

-   Room number validation is intentionally permissive but prevents strings with special characters; adjust regex if you need strict formats (e.g., letter+3 digits).
-   Description length prevents very short or extremely long messages and provides friendly re-prompts.
-   The flow uses inline keyboards for selection steps to reduce typing errors and keep payloads consistent with DB enums.

## Developer notes / next steps

-   Implement `client.submit_complaint()` (D.1 / D.2) to finalize submission.
-   Add storage persistence or conversation persistence if you want to survive bot restarts (PTB persistence backends).
-   Consider adding an explicit `CONFIRM` state if you want the user to review/confirm before final submission.
-   Optionally include photo upload step (accept `InputMedia` or ask for photo then store `file_id`/URL).

---

File generated: `conversation_flow.md` — use this as the authoritative flow doc for Phase 1 and update as the conversation changes.
