from io import BytesIO

from PIL import Image
import pytest

from app.images.schemas import ImageValidationError, validate_image_bytes
from app.images.storage import LocalStorage


def _image_bytes(format_name: str = "PNG", size: tuple[int, int] = (4, 3)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size, "white").save(buffer, format=format_name)
    return buffer.getvalue()


def test_validate_accepts_real_png_magic_and_returns_dimensions() -> None:
    result = validate_image_bytes(_image_bytes(), "image/png")

    assert result.mime_type == "image/png"
    assert result.width == 4
    assert result.height == 3


def test_validate_rejects_mime_magic_size_and_pixel_mismatches() -> None:
    with pytest.raises(ImageValidationError, match="MIME_MISMATCH"):
        validate_image_bytes(_image_bytes(), "image/jpeg")
    with pytest.raises(ImageValidationError, match="IMAGE_INVALID"):
        validate_image_bytes(b"not-an-image", "image/png")
    with pytest.raises(ImageValidationError, match="IMAGE_TOO_LARGE"):
        validate_image_bytes(_image_bytes(), "image/png", max_bytes=4)
    with pytest.raises(ImageValidationError, match="PIXELS_TOO_LARGE"):
        validate_image_bytes(_image_bytes(size=(10, 10)), "image/png", max_pixels=10)


def test_local_storage_uses_safe_namespaces_and_blocks_traversal(tmp_path) -> None:
    storage = LocalStorage(tmp_path)
    key = storage.save(b"bytes", namespace="private", suffix="png")

    assert key.startswith("private/")
    assert storage.read(key) == b"bytes"
    with pytest.raises(ValueError, match="INVALID_OBJECT_KEY"):
        storage.read("../outside")
