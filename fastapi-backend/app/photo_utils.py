"""
Photo utilities for image processing and thumbnail generation.

Uses Pillow (PIL) for image manipulation.
"""

from PIL import Image
import io
from typing import Tuple, Optional
import logging

logger = logging.getLogger("app.photo_utils")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    logger.addHandler(handler)

# Configuration
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_IMAGE_DIMENSION = 4000  # pixels
THUMBNAIL_SIZE = (256, 256)  # Thumbnail dimensions
ALLOWED_MIME_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def validate_image(file_data: bytes, file_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate image file.

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file size
    if len(file_data) > MAX_UPLOAD_SIZE:
        return False, f"File size exceeds {MAX_UPLOAD_SIZE / (1024*1024):.1f} MB limit"

    # Check extension
    ext = "." + file_name.split(".")[-1].lower() if "." in file_name else ""
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

    # Try to open and validate image
    try:
        img = Image.open(io.BytesIO(file_data))
        img.verify()  # Verify it's a valid image

        # Re-open for processing (verify() closes the image)
        img = Image.open(io.BytesIO(file_data))
        width, height = img.size

        # Check dimensions
        if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
            return False, f"Image dimensions exceed {MAX_IMAGE_DIMENSION}px"

        # Return True if all checks pass
        return True, None

    except Exception as e:
        logger.error(f"Image validation failed: {e}")
        return False, f"Invalid image file: {str(e)}"


def process_image(
    file_data: bytes, file_name: str
) -> Tuple[bytes, bytes, int, int, str]:
    """
    Process uploaded image: resize if needed and generate thumbnail.

    Returns:
        Tuple of (optimized_image_data, thumbnail_data, width, height, mime_type)
    """
    # Read original image
    img = Image.open(io.BytesIO(file_data))

    # Get original dimensions
    width, height = img.size

    # Convert to RGB if necessary (for PNG with transparency, etc.)
    if img.mode in ("RGBA", "LA", "P"):
        # Create white background
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Resize if image is too large
    max_dimension = 2048  # Max dimension for stored image
    if width > max_dimension or height > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)
        width, height = img.size
        logger.info(f"Resized image to {width}x{height}")

    # Save optimized image
    optimized_buffer = io.BytesIO()
    img.save(optimized_buffer, format="JPEG", quality=85, optimize=True)
    optimized_data = optimized_buffer.getvalue()

    # Generate thumbnail
    thumbnail = img.copy()
    thumbnail.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)

    thumbnail_buffer = io.BytesIO()
    thumbnail.save(thumbnail_buffer, format="JPEG", quality=75, optimize=True)
    thumbnail_data = thumbnail_buffer.getvalue()

    return optimized_data, thumbnail_data, width, height, "image/jpeg"


def get_image_dimensions(file_data: bytes) -> Tuple[int, int]:
    """Get image dimensions without fully processing the image."""
    try:
        img = Image.open(io.BytesIO(file_data))
        return img.size
    except Exception as e:
        logger.error(f"Failed to get image dimensions: {e}")
        return 0, 0


def get_mime_type(file_name: str) -> str:
    """Get MIME type from file extension."""
    ext = file_name.split(".")[-1].lower() if "." in file_name else ""
    mime_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
    }
    return mime_map.get(ext, "application/octet-stream")
