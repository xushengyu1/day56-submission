from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid5

from PIL import Image, ImageDraw
from app.auth.models import User
from app.auth.security import hash_password
from app.database import session_factory
from app.db.enums import (
    DataClass,
    ImagePurpose,
    ItemType,
    LocationArea,
    PublicCategory,
    RecordKind,
    RecordStatus,
    RedactionStatus,
    UserRole,
)
from app.images.models import ImageAsset
from app.items.models import ItemRecord
from app.matching.models import CandidateMatch


NAMESPACE = UUID("9f5d69f6-8f68-4f67-b76e-13155fc81e21")
BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = BACKEND_ROOT.parents[1]
IMAGE_ROOT = REPOSITORY_ROOT / "images"
STORAGE_ROOT = BACKEND_ROOT / "storage"


@dataclass(frozen=True)
class DemoCase:
    slug: str
    image_name: str | None
    name: str
    category: PublicCategory
    lost_description: str
    found_description: str
    lost_area: LocationArea
    found_area: LocationArea
    lost_location: str
    found_location: str
    score: int
    conflicts: tuple[str, ...] = ()


DEMO_CASES = (
    DemoCase(
        "resident-id",
        "images.jpeg",
        "居民身份证",
        PublicCategory.IDENTITY_CARD,
        "蓝色居民身份证，装在透明卡套中；姓名及号码不公开。",
        "拾到一张装在透明卡套中的居民身份证，敏感信息已脱敏。",
        LocationArea.CANTEEN,
        LocationArea.CANTEEN,
        "一食堂一楼靠窗座位",
        "一食堂一楼靠窗座位下方",
        96,
    ),
    DemoCase(
        "graduation-certificate",
        "毕业证.jpg",
        "红色毕业证书",
        PublicCategory.IDENTITY_CARD,
        "红色毕业证书外壳，封面有金色校徽与文字。",
        "拾到红色毕业证书一本，红色硬壳，封面为金色字样。",
        LocationArea.SCIENCE_BUILDING,
        LocationArea.SCIENCE_BUILDING,
        "科教楼报告厅",
        "科教楼报告厅后排",
        94,
    ),
    DemoCase(
        "laptop",
        "电脑.jpg",
        "灰色华为笔记本电脑",
        PublicCategory.ELECTRONICS,
        "灰色华为笔记本电脑，A 面中央有 HUAWEI 标志。",
        "拾到灰色华为笔记本电脑，合盖状态，外壳中央有品牌标志。",
        LocationArea.LIBRARY,
        LocationArea.LIBRARY,
        "图书馆三楼自习区",
        "图书馆三楼自习区充电桌",
        95,
    ),
    DemoCase(
        "laptop-bag",
        "电脑包.jpg",
        "深灰色手提电脑包",
        PublicCategory.OTHER_CATEGORY,
        "深灰色长方形手提电脑包，双提手，正面有窄装饰条。",
        "拾到深灰色手提电脑包一个，双提手，包面有竖向拼接。",
        LocationArea.TEACHING_BUILDING,
        LocationArea.TEACHING_BUILDING,
        "教学楼东区一楼",
        "教学楼东区一楼走廊",
        92,
    ),
    DemoCase(
        "notebook",
        "笔记本.jpg",
        "棕色皮面笔记本",
        PublicCategory.STATIONERY,
        "棕色皮面笔记本，封面左下角有压印图案，带棕色书签。",
        "拾到棕色皮面笔记本，左下角有压花，底部露出书签带。",
        LocationArea.LIBRARY,
        LocationArea.LIBRARY,
        "图书馆二楼阅览区",
        "图书馆二楼阅览区入口",
        97,
    ),
    DemoCase(
        "melody-tote",
        "美乐蒂托特包.jpg",
        "粉色美乐蒂托特包",
        PublicCategory.CLOTHING,
        "粉白色美乐蒂托特包，正面有卡通脸和草莓挂件。",
        "拾到粉色卡通托特包，正面是美乐蒂图案，挂着草莓毛线挂件。",
        LocationArea.DORMITORY,
        LocationArea.DORMITORY,
        "宿舍区 3 号楼门厅",
        "宿舍区 3 号楼门禁旁",
        96,
    ),
    DemoCase(
        "badminton-racket",
        "羽毛球拍.jpg",
        "尤尼克斯羽毛球拍",
        PublicCategory.OTHER_CATEGORY,
        "尤尼克斯羽毛球拍，黑色拍套上有白色 YONEX 标志。",
        "拾到一支带黑色拍套的羽毛球拍，拍套印有白色 YONEX 字样。",
        LocationArea.DORMITORY,
        LocationArea.DORMITORY,
        "宿舍区羽毛球场",
        "宿舍区羽毛球场 2 号场地",
        98,
    ),
    DemoCase(
        "sports-jacket",
        "衣服.jpeg",
        "红黑色运动外套",
        PublicCategory.CLOTHING,
        "红黑拼色连帽运动外套，胸前有白色 Under Armour 标志。",
        "拾到红黑拼色连帽外套，拉链款，胸前有白色运动品牌标志。",
        LocationArea.CANTEEN,
        LocationArea.CANTEEN,
        "二食堂二楼",
        "二食堂二楼靠楼梯座位",
        95,
    ),
    DemoCase(
        "umbrella-floor-conflict",
        None,
        "黑色折叠伞",
        PublicCategory.OTHER_CATEGORY,
        "黑色短柄折叠伞；记得是哑光直柄，可能遗失在教学楼三楼。",
        "黑色短柄折叠伞；实际为亮面弯柄，在教学楼二楼楼梯口拾到。",
        LocationArea.TEACHING_BUILDING,
        LocationArea.TEACHING_BUILDING,
        "教学楼三楼（失主回忆）",
        "教学楼二楼楼梯口",
        84,
        ("FLOOR_CONFLICT", "HANDLE_FEATURE_CONFLICT"),
    ),
)


def demo_id(label: str) -> UUID:
    return uuid5(NAMESPACE, label)


def item_type_for(category: PublicCategory) -> ItemType:
    if category is PublicCategory.IDENTITY_CARD:
        return ItemType.IDENTITY_DOCUMENT
    return ItemType.OTHER


def _public_image(source: Path, *, redact_identity: bool) -> tuple[bytes, str, str]:
    if redact_identity:
        image = Image.new("RGB", (800, 500), "#e8eef5")
        draw = ImageDraw.Draw(image)
        draw.rectangle((60, 60, 740, 440), fill="#c8d7e6", outline="#6b8ba4", width=4)
        draw.rectangle((110, 120, 300, 380), fill="#8799aa")
        draw.rectangle((350, 140, 680, 180), fill="#445566")
        draw.rectangle((350, 220, 680, 260), fill="#445566")
        draw.rectangle((350, 300, 680, 340), fill="#445566")
        output = BytesIO()
        image.save(output, format="PNG")
        return output.getvalue(), "png", "image/png"
    data = source.read_bytes()
    suffix = source.suffix.casefold().lstrip(".")
    return data, suffix, "image/jpeg"


def _write_asset(object_key: str, data: bytes) -> None:
    path = STORAGE_ROOT / object_key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


async def seed() -> None:
    missing = [case.image_name for case in DEMO_CASES if case.image_name and not (IMAGE_ROOT / case.image_name).is_file()]
    if missing:
        raise FileNotFoundError(f"missing demo images: {missing}")

    users = (
        ("demo-lin", "林晓", "linxiao.demo@example.test"),
        ("demo-chen", "陈晨", "chenchen.demo@example.test"),
        ("demo-wang", "王宁", "wangning.demo@example.test"),
    )
    password = "Demo123456!"
    password_hash = hash_password(password)
    now = datetime.now(timezone.utc).replace(microsecond=0)

    async with session_factory() as session:
        async with session.begin():
            demo_users: list[User] = []
            for label, username, email in users:
                user = await session.get(User, demo_id(label))
                if user is None:
                    user = User(id=demo_id(label), username=username, email=email, password_hash=password_hash, role=UserRole.USER)
                    session.add(user)
                else:
                    user.username = username
                    user.email = email
                    user.password_hash = password_hash
                demo_users.append(user)

            for index, case in enumerate(DEMO_CASES):
                lost_owner = demo_users[index % len(demo_users)]
                found_owner = demo_users[(index + 1) % len(demo_users)]
                event_time = now - timedelta(days=index + 1)
                pair: dict[RecordKind, ItemRecord] = {}
                for kind, owner, description, area, location in (
                    (RecordKind.LOST, lost_owner, case.lost_description, case.lost_area, case.lost_location),
                    (RecordKind.FOUND, found_owner, case.found_description, case.found_area, case.found_location),
                ):
                    record_id = demo_id(f"{case.slug}-{kind.value.casefold()}")
                    record = await session.get(ItemRecord, record_id)
                    values = {
                        "owner_user_id": owner.id,
                        "kind": kind,
                        "item_type": item_type_for(case.category),
                        "public_category": case.category,
                        "location_area": area,
                        "status": RecordStatus.PUBLISHED,
                        "name_public": case.name,
                        "description_public": description,
                        "event_time_exact": event_time,
                        "event_time_public": event_time.astimezone(timezone(timedelta(hours=8))).strftime("%Y年%m月%d日 %H:%M"),
                        "location_public": location,
                        "published_at": event_time + timedelta(hours=2),
                        "version": 1,
                    }
                    if record is None:
                        record = ItemRecord(id=record_id, **values)
                        session.add(record)
                    else:
                        for field, value in values.items():
                            setattr(record, field, value)
                    pair[kind] = record

                candidate_id = demo_id(f"{case.slug}-candidate")
                candidate = await session.get(CandidateMatch, candidate_id)
                candidate_values = {
                    "lost_record_id": pair[RecordKind.LOST].id,
                    "found_record_id": pair[RecordKind.FOUND].id,
                    "semantic_score": Decimal("40.00"),
                    "time_score": Decimal("20.00"),
                    "location_score": Decimal("14.00") if case.conflicts else Decimal("20.00"),
                    "completeness_score": Decimal(f"{case.score - 74 if case.conflicts else case.score - 80}.00"),
                    "total_score": Decimal(f"{case.score}.00"),
                    "reason_codes": ["CATEGORY_MATCH", "SEMANTIC_DESCRIPTION_MATCH", "TIME_WINDOW_MATCH", "SAME_LOCATION_AREA"],
                    "conflict_codes": list(case.conflicts),
                    "rule_version": "demo-v1",
                    "model_version": "demo-ai-semantic-v1",
                    "input_snapshot_hash": hashlib.sha256(case.slug.encode()).hexdigest(),
                }
                if candidate is None:
                    session.add(CandidateMatch(id=candidate_id, **candidate_values))
                else:
                    for field, value in candidate_values.items():
                        setattr(candidate, field, value)

                if case.image_name is None:
                    continue
                source = IMAGE_ROOT / case.image_name
                public_data, suffix, mime_type = _public_image(source, redact_identity=case.image_name == "images.jpeg")
                for kind, record in pair.items():
                    object_key = f"public/demo/{case.slug}-{kind.value.casefold()}.{suffix}"
                    _write_asset(object_key, public_data)
                    asset_id = demo_id(f"{case.slug}-{kind.value.casefold()}-public-image")
                    asset = await session.get(ImageAsset, asset_id)
                    asset_values = {
                        "record_id": record.id,
                        "uploader_user_id": record.owner_user_id,
                        "purpose": ImagePurpose.PUBLIC_REDACTED,
                        "data_class": DataClass.PUBLIC,
                        "object_key": object_key,
                        "sha256": hashlib.sha256(public_data).hexdigest(),
                        "mime_type": mime_type,
                        "size_bytes": len(public_data),
                        "redaction_status": RedactionStatus.CONFIRMED,
                    }
                    if asset is None:
                        session.add(ImageAsset(id=asset_id, **asset_values))
                    else:
                        for field, value in asset_values.items():
                            setattr(asset, field, value)

                original_data = source.read_bytes()
                original_suffix = source.suffix.casefold().lstrip(".")
                original_key = f"private/demo/{case.slug}-found-original.{original_suffix}"
                _write_asset(original_key, original_data)
                original_id = demo_id(f"{case.slug}-found-original-image")
                original = await session.get(ImageAsset, original_id)
                original_values = {
                    "record_id": pair[RecordKind.FOUND].id,
                    "uploader_user_id": pair[RecordKind.FOUND].owner_user_id,
                    "purpose": ImagePurpose.FINDER_ORIGINAL,
                    "data_class": DataClass.PRIVATE,
                    "object_key": original_key,
                    "sha256": hashlib.sha256(original_data).hexdigest(),
                    "mime_type": "image/jpeg",
                    "size_bytes": len(original_data),
                    "redaction_status": RedactionStatus.NOT_REQUIRED,
                }
                if original is None:
                    session.add(ImageAsset(id=original_id, **original_values))
                else:
                    for field, value in original_values.items():
                        setattr(original, field, value)

    print(f"seeded users={len(users)} records={len(DEMO_CASES) * 2} candidates={len(DEMO_CASES)} images={sum(case.image_name is not None for case in DEMO_CASES) * 3}")
    print("demo login: linxiao.demo@example.test / Demo123456!")


if __name__ == "__main__":
    asyncio.run(seed())
