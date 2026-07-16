from io import BytesIO

from PIL import Image
import pytest

from app.images.redaction import redact_image_bytes
from app.images.schemas import RedactionRegion


def _png() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (4, 4), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def test_redaction_overwrites_region_and_keeps_image_valid() -> None:
    redacted = redact_image_bytes(_png(), RedactionRegion(x=1, y=1, width=2, height=2))
    image = Image.open(BytesIO(redacted)).convert("RGB")

    assert image.getpixel((1, 1)) == (0, 0, 0)
    assert image.getpixel((0, 0)) == (255, 255, 255)


def test_redaction_rejects_empty_or_out_of_bounds_region() -> None:
    with pytest.raises(ValueError, match="REDACTION_REGION_INVALID"):
        redact_image_bytes(_png(), RedactionRegion(x=0, y=0, width=0, height=1))
    with pytest.raises(ValueError, match="REDACTION_REGION_INVALID"):
        redact_image_bytes(_png(), RedactionRegion(x=3, y=3, width=2, height=2))
