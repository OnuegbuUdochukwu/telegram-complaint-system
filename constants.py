# Constants for the Complaint Management System Bot

# --- Application Configuration ---
# Constants for data that is frequently accessed or used across modules.

# The current set of Hostels available for selection
HOSTELS = ["Bethel", "Canaan", "Dorcas", "Shiloh", "Zion"]

# The current set of Complaint Categories for facility issues
COMPLAINT_CATEGORIES = [
    "Plumbing Issue", 
    "Electrical Fault", 
    "Structural Damage", 
    "HVAC/Fan Repair", 
    "Cleaning/Sanitation", 
    "Other"
]

# --- ConversationHandler States (The State Machine) ---
# These integers represent the distinct steps or stages in the /report conversation flow.
# They MUST be unique positive integers.

# Entry point/initial state for a conversation (typically starts after the ENTRY_POINT handler)
SELECT_HOSTEL = 1

# State where the bot expects the user to input their room number
GET_ROOM_NUMBER = 2

# State where the bot expects the user to select the complaint category
SELECT_CATEGORY = 3

# State where the bot expects the user to input the detailed description of the issue
GET_DESCRIPTION = 4

# The final state where the bot processes and submits the complaint
SUBMIT_COMPLAINT = 5

# State for handling cancellation at any point
CANCEL = 6 

# List of all states for reference (useful for debugging/logging)
ALL_STATES = [SELECT_HOSTEL, GET_ROOM_NUMBER, SELECT_CATEGORY, GET_DESCRIPTION, SUBMIT_COMPLAINT]
