import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, User, Message, CallbackQuery, Chat
from telegram.ext import ContextTypes, ConversationHandler
from main import (
    report_entry, select_hostel_callback, get_room_number, 
    select_category_callback, get_description, select_severity_callback,
    SELECT_HOSTEL, GET_ROOM_NUMBER, SELECT_CATEGORY, GET_DESCRIPTION, SELECT_SEVERITY, SUBMIT_COMPLAINT, ATTACH_PHOTOS
)
from merged_constants import HOSTELS

@pytest.fixture
def mock_update_context():
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 12345
    update.effective_user.first_name = "TestUser"
    update.effective_message = MagicMock(spec=Message)
    update.message = update.effective_message
    update.callback_query = MagicMock(spec=CallbackQuery)
    
    # Setup async methods
    update.message.reply_text = AsyncMock()
    update.message.reply_html = AsyncMock()
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    
    return update, context

@pytest.mark.asyncio
async def test_report_entry(mock_update_context):
    update, context = mock_update_context
    state = await report_entry(update, context)
    
    assert state == SELECT_HOSTEL
    assert context.user_data['complaint']['telegram_user_id'] == "12345"
    update.message.reply_text.assert_called_once()

@pytest.mark.asyncio
async def test_select_hostel(mock_update_context):
    update, context = mock_update_context
    update.callback_query.data = "hostel_Daniel"
    update.callback_query.from_user.id = 12345
    context.user_data['complaint'] = {}

    state = await select_hostel_callback(update, context)
    
    assert state == GET_ROOM_NUMBER
    assert context.user_data['complaint']['hostel'] == "Daniel"
    update.callback_query.edit_message_text.assert_called_once()

@pytest.mark.asyncio
async def test_get_room_number_valid(mock_update_context):
    update, context = mock_update_context
    update.message.text = "A101"
    context.user_data['complaint'] = {}

    state = await get_room_number(update, context)
    
    assert state == SELECT_CATEGORY
    assert context.user_data['complaint']['room_number'] == "A101"
    assert context.user_data['complaint']['wing'] == "A"

@pytest.mark.asyncio
async def test_get_room_number_invalid(mock_update_context):
    update, context = mock_update_context
    update.message.text = "InvalidRoom"
    context.user_data['complaint'] = {}

    state = await get_room_number(update, context)
    
    assert state == GET_ROOM_NUMBER
    # Should reply with warning
    update.message.reply_text.assert_called()
    assert "Invalid room number" in update.message.reply_text.call_args[0][0] or \
           "valid room number" in update.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_select_category_callback(mock_update_context):
    update, context = mock_update_context
    update.callback_query.data = "category_Plumbing / Water"
    update.callback_query.from_user.id = 12345
    context.user_data['complaint'] = {}

    state = await select_category_callback(update, context)
    
    assert state == GET_DESCRIPTION
    # Note: the code might store the display label or the key depending on implementation details
    # The current impl splits by '_' and takes the rest. 
    # category_Plumbing / Water -> Plumbing / Water
    assert context.user_data['complaint']['category'] == "Plumbing / Water"

@pytest.mark.asyncio
async def test_get_description_valid(mock_update_context):
    update, context = mock_update_context
    update.message.text = "This is a valid description of the issue."
    context.user_data['complaint'] = {}

    state = await get_description(update, context)
    
    assert state == SELECT_SEVERITY
    assert context.user_data['complaint']['description'] == update.message.text

@pytest.mark.asyncio
async def test_get_description_too_short(mock_update_context):
    update, context = mock_update_context
    update.message.text = "Short"
    context.user_data['complaint'] = {}

    state = await get_description(update, context)
    
    assert state == GET_DESCRIPTION # stay in same state
    update.message.reply_text.assert_called()

# Mock client.submit_complaint for the final step test
@pytest.mark.asyncio
async def test_select_severity_and_submit(mock_update_context, monkeypatch):
    update, context = mock_update_context
    update.callback_query.data = "severity_high"
    
    # Pre-populate required data
    context.user_data['complaint'] = {
        "telegram_user_id": "12345",
        "hostel": "Daniel",
        "wing": "A",
        "room_number": "A101",
        "category": "Plumbing / Water",
        "description": "Fix the pipe",
    }

    # Mock the client submission
    mock_submit = AsyncMock(return_value={"complaint_id": "COMP-123", "status": "success"})
    monkeypatch.setattr("main.client_submit", mock_submit)

    state = await select_severity_callback(update, context)
    
    assert state == ATTACH_PHOTOS
    assert context.user_data['complaint']['severity'] == "high"
    assert context.user_data['current_complaint_id'] == "COMP-123"
    mock_submit.assert_called_once()
