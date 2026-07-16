from __future__ import annotations

from io import BytesIO

from PIL import Image, UnidentifiedImageError

from app.images.schemas import RedactionRegion


def redact_image_bytes(data: bytes, region: RedactionRegion) -> bytes:
    try:
        image = Image.open(BytesIO(data)).convert("RGBA")
    except (UnidentifiedImageError, OSError):
        raise ValueError("IMAGE_INVALID") from None
    if (
        region.width <= 0
        or region.height <= 0
        or region.x < 0
        or region.y < 0
        or region.x + region.width > image.width
        or region.y + region.height > image.height
    ):
        raise ValueError("REDACTION_REGION_INVALID")
    pixels = image.load()
    for y in range(region.y, region.y + region.height):
        for x in range(region.x, region.x + region.width):
            pixels[x, y] = (0, 0, 0, 255)
    output = BytesIO()
    image.save(output, format="PNG", optimize=False)
    return output.getvalue()
