import pytest

from app.db.enums import ItemType, LocationArea, PublicCategory
from app.items.catalog import (
    build_public_embedding_text,
    item_type_for,
    location_public_for,
)


@pytest.mark.parametrize(
    ("category", "expected"),
    [
        (PublicCategory.ELECTRONICS, ItemType.OTHER),
        (PublicCategory.IDENTITY_CARD, ItemType.IDENTITY_DOCUMENT),
        (PublicCategory.CLOTHING, ItemType.OTHER),
        (PublicCategory.STATIONERY, ItemType.OTHER),
        (PublicCategory.OTHER_CATEGORY, ItemType.OTHER),
    ],
)
def test_public_category_maps_to_verification_type(category, expected):
    assert item_type_for(category) is expected


@pytest.mark.parametrize(
    ("area", "label"),
    [
        (LocationArea.DORMITORY, "宿舍区"),
        (LocationArea.CANTEEN, "食堂"),
        (LocationArea.TEACHING_BUILDING, "教学楼"),
        (LocationArea.SCIENCE_BUILDING, "科教楼"),
        (LocationArea.LIBRARY, "图书馆"),
    ],
)
def test_location_area_has_one_public_label(area, label):
    assert location_public_for(area) == label


def test_embedding_text_contains_public_detail_only():
    text = build_public_embedding_text(
        name_public="黑色折叠伞",
        description_public="教学楼 B 区 302 教室，伞柄有公开划痕",
        location_public="教学楼",
    )

    assert text == "黑色折叠伞\n教学楼 B 区 302 教室，伞柄有公开划痕\n教学楼"
    assert "字母A" not in text
