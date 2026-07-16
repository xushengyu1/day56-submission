from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, UnidentifiedImageError


class ImageValidationError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class ImageValidation:
    mime_type: str
    format_name: str
    width: int
    height: int
    size_bytes: int


@dataclass(frozen=True)
class RedactionRegion:
    x: int
    y: int
    width: int
    height: int


_MIME_TO_FORMAT = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}


def validate_image_bytes(
    data: bytes,
    declared_mime: str,
    *,
    max_bytes: int = 10 * 1024 * 1024,
    max_pixels: int = 20_000_000,
) -> ImageValidation:
    if len(data) > max_bytes:
        raise ImageValidationError("IMAGE_TOO_LARGE")
    expected_format = _MIME_TO_FORMAT.get(declared_mime.casefold())
    if expected_format is None:
        raise ImageValidationError("MIME_NOT_ALLOWED")
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format != expected_format:
                raise ImageValidationError("MIME_MISMATCH")
            image.verify()
        with Image.open(BytesIO(data)) as image:
            width, height = image.size
            if width <= 0 or height <= 0 or width * height > max_pixels:
                raise ImageValidationError("PIXELS_TOO_LARGE")
    except ImageValidationError:
        raise
    except (UnidentifiedImageError, OSError, ValueError):
        raise ImageValidationError("IMAGE_INVALID") from None
    return ImageValidation(
        mime_type=declared_mime.casefold(),
        format_name=expected_format,
        width=width,
        height=height,
        size_bytes=len(data),
    )
