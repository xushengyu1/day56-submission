from app.db.enums import ItemType, LocationArea, PublicCategory


_LOCATION_LABELS = {
    LocationArea.DORMITORY: "宿舍区",
    LocationArea.CANTEEN: "食堂",
    LocationArea.TEACHING_BUILDING: "教学楼",
    LocationArea.SCIENCE_BUILDING: "科教楼",
    LocationArea.LIBRARY: "图书馆",
}


def item_type_for(category: PublicCategory) -> ItemType:
    if category is PublicCategory.IDENTITY_CARD:
        return ItemType.IDENTITY_DOCUMENT
    return ItemType.OTHER


def location_public_for(area: LocationArea) -> str:
    return _LOCATION_LABELS[area]


def build_public_embedding_text(
    *, name_public: str, description_public: str, location_public: str
) -> str:
    return "\n".join(
        (name_public.strip(), description_public.strip(), location_public.strip())
    )
