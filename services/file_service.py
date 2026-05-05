import os
import uuid
from pathlib import Path

from flask import current_app
from werkzeug.utils import secure_filename

from constants import ALLOWED_IMAGE_EXTENSIONS


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
    )


def _validate_image_file(file_storage, original_filename):
    content_type = (getattr(file_storage, "mimetype", "") or "").lower()
    allowed_mime_types = {
        "image/png",
        "image/jpeg",
        "image/webp",
        "image/gif",
    }

    if content_type and content_type not in allowed_mime_types:
        raise ValueError(
            "Можна завантажувати лише зображення у форматах png, jpg, jpeg, webp або gif"
        )

    if "." not in original_filename:
        raise ValueError(
            "Файл повинен мати розширення: png, jpg, jpeg, webp або gif"
        )

    if not allowed_file(original_filename):
        raise ValueError(
            "Дозволені лише зображення: png, jpg, jpeg, webp, gif"
        )


def save_uploaded_image(file_storage, folder_name):
    if not file_storage:
        return None

    original_filename = (file_storage.filename or "").strip()
    if not original_filename:
        return None

    _validate_image_file(file_storage, original_filename)

    filename = secure_filename(original_filename)
    if not filename or "." not in filename:
        raise ValueError("Некоректне ім’я файлу")

    ext = filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    upload_root = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    target_folder = (upload_root / folder_name).resolve()

    if upload_root not in target_folder.parents and target_folder != upload_root:
        raise ValueError("Некоректна папка для завантаження")

    os.makedirs(target_folder, exist_ok=True)

    save_path = target_folder / unique_name
    file_storage.save(save_path)

    return f"/static/uploads/{folder_name}/{unique_name}"
