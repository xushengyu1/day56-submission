from io import BytesIO
from typing import cast

import pytest
from fastapi import UploadFile
from PIL import Image
from starlette.datastructures import Headers

from app.api.errors import APIError
from app.api.routes.found_records import extract_preview
from app.auth.models import User
from app.multimodal.mock import MockMultimodalAdapter


def _png() -> bytes:
    output = BytesIO()
    Image.new("RGB", (4, 4), "white").save(output, format="PNG")
    return output.getvalue()


def _upload(data: bytes, content_type: str = "image/png") -> UploadFile:
    return UploadFile(
        BytesIO(data),
        filename="item.png",
        headers=Headers({"content-type": content_type}),
    )


@pytest.mark.asyncio
async def test_preview_extraction_returns_public_description_without_a_draft() -> None:
    response = await extract_preview(
        file=_upload(_png()),
        _user=cast(User, object()),
        adapter=MockMultimodalAdapter(),
    )

    assert response.suggested_description
    assert response.status.value == "SUCCEEDED"


@pytest.mark.asyncio
async def test_preview_extraction_rejects_invalid_image_bytes() -> None:
    with pytest.raises(APIError) as captured:
        await extract_preview(
            file=_upload(b"not-an-image"),
            _user=cast(User, object()),
            adapter=MockMultimodalAdapter(),
        )

    assert captured.value.code == "IMAGE_INVALID"
