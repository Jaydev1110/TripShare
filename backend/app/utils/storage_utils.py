import os
from datetime import datetime
from uuid import UUID
from io import BytesIO
from PIL import Image

def build_storage_path(group_id: UUID, uploader_id: UUID, filename: str) -> str:
    """
    Constructs a storage path: photos/<group_id>/<uploader_id>/<timestamp>_<filename>
    """
    timestamp = int(datetime.utcnow().timestamp())
    # Basic sanitization of filename
    safe_filename = "".join([c for c in filename if c.isalnum() or c in "._-"])
    return f"photos/{group_id}/{uploader_id}/{timestamp}_{safe_filename}"

def generate_thumbnail(file_bytes: bytes, max_size: tuple = (300, 300)) -> bytes:
    """
    Generates a thumbnail from image bytes.
    """
    img = Image.open(BytesIO(file_bytes))
    img.thumbnail(max_size)
    
    thumb_io = BytesIO()
    # Save as JPEG for consistency and size
    img = img.convert("RGB")
    img.save(thumb_io, format="JPEG", quality=85)
    thumb_io.seek(0)
    
    return thumb_io.getvalue()
