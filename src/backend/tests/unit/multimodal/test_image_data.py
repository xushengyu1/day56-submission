import pytest

from app.multimodal.image_data import encode_image_data_url


@pytest.mark.parametrize(
    ("suffix", "media_type"),
    [
        (".jpg", "image/jpeg"),
        ("jpeg", "image/jpeg"),
        (".png", "image/png"),
        ("webp", "image/webp"),
    ],
)
def test_encode_image_data_url_uses_allowlisted_media_type(
    suffix: str, media_type: str
) -> None:
    result = encode_image_data_url(b"synthetic", suffix)

    assert result == f"data:{media_type};base64,c3ludGhldGlj"


@pytest.mark.parametrize(("data", "suffix"), [(b"", ".png"), (b"x", ".gif")])
def test_encode_image_data_url_rejects_empty_or_unsupported_input(
    data: bytes, suffix: str
) -> None:
    with pytest.raises(ValueError, match="IMAGE_DATA_INVALID"):
        encode_image_data_url(data, suffix)
