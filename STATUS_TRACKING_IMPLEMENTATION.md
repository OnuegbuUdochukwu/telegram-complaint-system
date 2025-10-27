# Status Tracking Implementation

## Overview
Enhanced the complaint bot to allow users to track the status of their submitted complaints with a clear, user-friendly interface.

## Features Implemented

### 1. Enhanced Commands

#### `/status` - View All Your Complaints
- Shows all complaints submitted by the user
- Displays status with emoji indicators
- Shows essential details: Complaint ID, Hostel, Category, Status
- Paginated view (shows up to 10 complaints at a time)

#### `/mycomplaints` - Alias for Status
- Alternative command name for convenience
- Same functionality as `/status`

### 2. Status Lifecycle

The system uses the following status lifecycle:

```
📝 Reported → 🔧 In Progress → ✅ Resolved
                ↓
           ⏸️ On Hold
           ❌ Rejected (if inapplicable)
```

**Status Indicators:**
- 📝 **Reported** - Complaint submitted, pending review
- 🔧 **In Progress** - Complaint is being worked on
- ⏸️ **On Hold** - Temporarily paused for review/discussion
- ✅ **Resolved** - Issue has been fixed
- ✔️ **Closed** - Complaint completed and closed
- ❌ **Rejected** - Complaint was not applicable or invalid

### 3. User Experience Improvements

#### Welcome Message
- Updated to show all available commands
- Includes status lifecycle visualization
- Clear instructions on how to get started

#### Status Display Format
```
📋 Your Complaints

1. 🔧 In Progress
   ID: abc12345
   Hostel: John | Category: plumbing

2. ✅ Resolved
   ID: def67890
   Hostel: Joseph | Category: electrical
```

### 4. Backend API Enhancement

#### New Filter Parameter
Added `telegram_user_id` parameter to `/api/v1/complaints` endpoint:

```
GET /api/v1/complaints?telegram_user_id={user_id}
```

**Response Format:**
```json
{
  "items": [
    {
      "id": "complaint-uuid",
      "telegram_user_id": "user-id",
      "hostel": "John",
      "room_number": "A101",
      "category": "plumbing",
      "description": "Leaking sink",
      "severity": "medium",
      "status": "in_progress",
      "created_at": "2024-10-21T10:00:00Z",
      "updated_at": "2024-10-22T14:30:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

#### Public Access for Bot
The API allows public access (no authentication required) when filtering by `telegram_user_id`, enabling the bot to fetch user complaints without requiring authentication tokens.

### 5. Updated Client Functions

#### `get_user_complaints(telegram_user_id, page, page_size)`
- Fetches all complaints for a specific user
- Supports pagination
- Returns mock data if backend is not available
- Includes retry logic for network resilience

## Usage Examples

### For Users

1. **Submit a complaint:**
   ```
   User: /report
   Bot: [Guides through complaint submission]
   User: [Enters complaint details]
   Bot: ✅ Your complaint has been submitted successfully!
        Complaint ID: abc-123-def-456
   ```

2. **Check status:**
   ```
   User: /status
   Bot: ⏳ Fetching your complaints...
        📋 Your Complaints
        1. 🔧 In Progress
           ID: abc12345
           Hostel: John | Category: plumbing
        2. ✅ Resolved
           ID: def67890
           Hostel: Joseph | Category: electrical
   ```

3. **No complaints:**
   ```
   User: /status
   Bot: 📋 You haven't submitted any complaints yet.
        Use /report to submit a new complaint.
   ```

## Technical Implementation

### Files Modified

1. **`main.py`** (Bot Logic)
   - Enhanced `start_command` to show status lifecycle
   - Updated `help_command` to include new commands
   - Added `get_my_complaints` function for fetching user complaints
   - Implemented formatted status display with emojis
   - Added `/status` and `/mycomplaints` command handlers

2. **`client.py`** (Backend Client)
   - Added `get_user_complaints()` function
   - Implements retry logic
   - Provides mock data fallback for testing

3. **`fastapi-backend/app/main.py`** (Backend API)
   - Added `telegram_user_id` query parameter to complaints endpoint
   - Allowed public access when filtering by telegram_user_id
   - Maintains RBAC for admin/porter dashboard access

### Security Considerations

- **User Isolation**: When filtering by `telegram_user_id`, users can only see their own complaints
- **No Authentication Required**: Bot users can check their own status without logging in
- **Admin/Porter Access**: Dashboard users still require authentication and are subject to RBAC
- **Rate Limiting**: Consider implementing rate limits to prevent abuse

## Benefits

1. **User Empowerment**: Users can track the progress of their complaints in real-time
2. **Transparency**: Clear status lifecycle shows where each complaint stands
3. **Easy Access**: Simple commands (`/status` or `/mycomplaints`) make it effortless to check
4. **Visual Feedback**: Emoji indicators provide quick status understanding
5. **No Login Required**: Users can check status without authentication barriers

## Future Enhancements

Potential improvements for status tracking:

1. **Real-time Notifications**: Notify users when their complaint status changes
2. **Detailed Status View**: Show full complaint details including description and photos
3. **Status History**: Track status changes over time
4. **Estimated Resolution Time**: Provide ETA based on complaint type
5. **Photo Upload**: Allow users to add photos to existing complaints
6. **Status Filters**: Allow filtering by status (e.g., show only resolved complaints)
7. **Reminders**: Send reminders for unresolved complaints
8. **Feedback System**: Allow users to rate resolution quality

## Testing

To test the status tracking functionality:

1. **Submit a complaint:**
   ```
   /report
   [Follow the flow to submit a complaint]
   ```

2. **Check status:**
   ```
   /status
   ```

3. **View your complaints:**
   ```
   /mycomplaints
   ```

All commands should work seamlessly and display complaint status with the appropriate emoji indicators.

## Status Lifecycle Explanation

The status lifecycle ensures that users understand the journey of their complaint:

- **📝 Reported**: Initial submission - the complaint has been logged
- **🔧 In Progress**: Maintenance team has started working on it
- **⏸️ On Hold**: Temporarily stopped (maybe needs parts, approval, etc.)
- **✅ Resolved**: The issue has been fixed
- **✔️ Closed**: Official closure after user confirmation
- **❌ Rejected**: Complaint was not valid or applicable

This transparency helps users understand where their complaint is in the resolution process.

## Commands Summary

- `/start` - Welcome message with status lifecycle info
- `/report` - Submit a new complaint
- `/status` - View all your complaints with status
- `/mycomplaints` - Alias for /status
- `/help` - Show available commands
- `/cancel` - Cancel current operation

## Notes

- Status checks work without authentication (users see only their own complaints)
- Mock data is provided when backend is not available for testing
- All commands include helpful error messages
- Network issues are handled gracefully with retry logic
- The system maintains backward compatibility with existing commands

---

Document version: 2025-10-21

