import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, User, Message, PhotoSize, File
from telegram.ext import ContextTypes, ConversationHandler
from main import handle_photo_upload, ATTACH_PHOTOS

@pytest.fixture
def mock_update_context():
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 12345
    update.message = MagicMock(spec=Message)
    
    # Setup async reply
    update.message.reply_text = AsyncMock()
    # safe_reply_to_update uses effective_message.reply_text
    update.effective_message = update.message
    
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.bot = MagicMock()
    
    return update, context

@pytest.mark.asyncio
async def test_handle_photo_upload_success(mock_update_context, monkeypatch):
    update, context = mock_update_context
    
    # Setup state
    context.user_data['current_complaint_id'] = "COMP-123"
    
    # Mock Photo data
    photo_small = MagicMock(spec=PhotoSize); photo_small.file_id = "small_id"; photo_small.file_size = 100
    photo_large = MagicMock(spec=PhotoSize); photo_large.file_id = "large_id"; photo_large.file_size = 1000
    update.message.photo = [photo_small, photo_large]
    
    # Mock Telegram File retrieval and download
    mock_file = MagicMock(spec=File)
    mock_file.download_as_bytearray = AsyncMock(return_value=bytearray(b"fake_image_data"))
    context.bot.get_file = AsyncMock(return_value=mock_file)
    
    # Mock client upload
    mock_upload = AsyncMock(return_value={"id": "PHOTO-999", "file_url": "http://s3/photo.jpg"})
    monkeypatch.setattr("main.client_upload_photo", mock_upload)
    
    state = await handle_photo_upload(update, context)
    
    assert state == ATTACH_PHOTOS
    
    # Verify we fetched the *last* (largest) photo
    context.bot.get_file.assert_called_once_with("large_id")
    
    # Verify download was called
    mock_file.download_as_bytearray.assert_called_once()
    
    # Verify upload was called with correct data
    mock_upload.assert_called_once()
    args = mock_upload.call_args
    assert args[0][0] == "COMP-123" # complaint_id
    assert args[0][1] == b"fake_image_data" # bytes
    assert args[0][2] == "COMP-123_large_id.jpg" # filename

@pytest.mark.asyncio
async def test_handle_photo_no_context(mock_update_context):
    """FAIL: User sends photo but hasn't started a report (no complaint_id)."""
    update, context = mock_update_context
    context.user_data = {} # Empty
    
    state = await handle_photo_upload(update, context)
    
    assert state == ConversationHandler.END
    update.message.reply_text.assert_called_with("No complaint context found. Start a new report with /report.")

@pytest.mark.asyncio
async def test_handle_photo_download_failed(mock_update_context, monkeypatch):
    """FAIL: Telegram download fails."""
    update, context = mock_update_context
    context.user_data['current_complaint_id'] = "COMP-123"
    
    photo = MagicMock(spec=PhotoSize); photo.file_id = "fid"; photo.file_size=100
    update.message.photo = [photo]
    
    # Mock get_file failure
    context.bot.get_file = AsyncMock(side_effect=Exception("Telegram connection error"))
    
    state = await handle_photo_upload(update, context)
    
    assert state == ATTACH_PHOTOS # Should stay in state to allow retry
    # Verify user was notified
    call_args = update.message.reply_text.call_args[0][0]
    assert "Could not download" in call_args

@pytest.mark.asyncio
async def test_handle_photo_upload_failed(mock_update_context, monkeypatch):
    """FAIL: Backend upload fails."""
    update, context = mock_update_context
    context.user_data['current_complaint_id'] = "COMP-123"
    
    photo = MagicMock(spec=PhotoSize); photo.file_id = "fid"; photo.file_size=100
    update.message.photo = [photo]
    
    mock_file = MagicMock(spec=File)
    mock_file.download_as_bytearray = AsyncMock(return_value=bytearray(b"data"))
    context.bot.get_file = AsyncMock(return_value=mock_file)
    
    # Mock upload failure
    mock_upload = AsyncMock(side_effect=Exception("S3 error"))
    monkeypatch.setattr("main.client_upload_photo", mock_upload)
    
    state = await handle_photo_upload(update, context)
    
    assert state == ATTACH_PHOTOS
    # Verify user was notified
    call_args = update.message.reply_text.call_args[0][0]
    assert "Failed to upload photo" in call_args
