from base64 import b64encode


_MEDIA_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}


def encode_image_data_url(data: bytes, suffix: str) -> str:
    extension = suffix.casefold().lstrip(".")
    media_type = _MEDIA_TYPES.get(extension)
    if not data or media_type is None:
        raise ValueError("IMAGE_DATA_INVALID")
    payload = b64encode(data).decode("ascii")
    return f"data:{media_type};base64,{payload}"
