"""File storage utilities."""

import os
import uuid
from typing import Optional, Tuple
from flask import current_app
from werkzeug.datastructures import FileStorage


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed.

    Args:
        filename: Original filename

    Returns:
        True if extension is allowed
    """
    if not filename:
        return False
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", {"pdf"})
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def save_file(file: FileStorage) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    """Save uploaded file to storage.

    Args:
        file: Werkzeug FileStorage object

    Returns:
        Tuple of (unique_filename, file_path, file_size) or (None, None, None) on error
    """
    if not file or not file.filename:
        return None, None, None

    # Generate unique filename
    ext = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else ""
    unique_filename = f"{uuid.uuid4()}.{ext}" if ext else str(uuid.uuid4())

    # Ensure upload directory exists (use absolute path)
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "storage/uploads")
    if not os.path.isabs(upload_folder):
        # Make relative paths relative to the app root
        upload_folder = os.path.join(current_app.root_path, upload_folder)
    os.makedirs(upload_folder, exist_ok=True)

    # Save file
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)

    # Get file size
    file_size = os.path.getsize(file_path)

    return unique_filename, file_path, file_size


def delete_file(file_path: str) -> bool:
    """Delete file from storage.

    Args:
        file_path: Path to file

    Returns:
        True if deleted successfully
    """
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except OSError:
        return False


def get_file_path(filename: str) -> Optional[str]:
    """Get full path to stored file.

    Args:
        filename: Unique filename

    Returns:
        Full file path or None if not found
    """
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "storage/uploads")
    file_path = os.path.join(upload_folder, filename)

    if os.path.exists(file_path):
        return file_path
    return None
