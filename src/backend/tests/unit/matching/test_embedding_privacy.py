from datetime import datetime, timezone
from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import LocationArea, PublicCategory
from app.matching.service import create_lost_record


class CaptureEmbeddingAdapter:
    model = "capture-v1"
    dimension = 3

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        return [[0.1, 0.2, 0.3] for _ in texts]


class AddOnlySession:
    def __init__(self) -> None:
        self.added: list[object] = []

    def add(self, value: object) -> None:
        self.added.append(value)


@pytest.mark.asyncio
async def test_lost_embedding_contains_public_detail_and_no_hidden_text() -> None:
    adapter = CaptureEmbeddingAdapter()
    session = AddOnlySession()

    record = await create_lost_record(
        cast(AsyncSession, session),
        owner_user_id=uuid4(),
        public_category=PublicCategory.OTHER_CATEGORY,
        location_area=LocationArea.TEACHING_BUILDING,
        event_time=datetime(2026, 7, 16, 10, 0, tzinfo=timezone.utc),
        name_public="黑色折叠伞",
        description_public="教学楼 B 区 302 教室，伞柄有公开划痕",
        embedding_adapter=adapter,
    )

    assert adapter.calls == [
        ["黑色折叠伞\n教学楼 B 区 302 教室，伞柄有公开划痕\n教学楼"]
    ]
    assert "伞套内侧字母A" not in str(adapter.calls)
    assert session.added == [record]
