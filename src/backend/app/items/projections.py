from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import DataClass, ImagePurpose, RedactionStatus
from app.images.models import ImageAsset
from app.items.models import ItemRecord
from app.items.schemas import ItemRecordPublic
from app.matching.models import CandidateMatch
from app.reviews.models import Claim
from app.verification.models import IdentityDocumentSecret


async def project_records(
    session: AsyncSession,
    records: Sequence[ItemRecord],
    *,
    actor_id: UUID,
) -> list[ItemRecordPublic]:
    if not records:
        return []

    record_ids = [record.id for record in records]

    # Get PUBLIC_REDACTED images
    public_image_rows = await session.execute(
        select(ImageAsset.record_id, ImageAsset.id)
        .where(
            ImageAsset.record_id.in_(record_ids),
            ImageAsset.purpose == ImagePurpose.PUBLIC_REDACTED,
            ImageAsset.data_class == DataClass.PUBLIC,
            ImageAsset.redaction_status == RedactionStatus.CONFIRMED,
        )
        .order_by(ImageAsset.created_at.desc(), ImageAsset.id)
    )
    image_ids: dict[UUID, UUID] = {}
    for record_id, asset_id in public_image_rows:
        image_ids.setdefault(record_id, asset_id)

    # For records owned by the actor, also get their PRIVATE images if no public image exists
    owned_record_ids = [r.id for r in records if r.owner_user_id == actor_id]
    if owned_record_ids:
        missing_ids = [rid for rid in owned_record_ids if rid not in image_ids]
        if missing_ids:
            private_image_rows = await session.execute(
                select(ImageAsset.record_id, ImageAsset.id)
                .where(
                    ImageAsset.record_id.in_(missing_ids),
                    ImageAsset.purpose.in_([ImagePurpose.FINDER_ORIGINAL, ImagePurpose.OWNER_SUPPORT]),
                    ImageAsset.data_class == DataClass.PRIVATE,
                    ImageAsset.uploader_user_id == actor_id,
                )
                .order_by(ImageAsset.created_at.desc(), ImageAsset.id)
            )
            for record_id, asset_id in private_image_rows:
                image_ids.setdefault(record_id, asset_id)

    identity_rows = await session.execute(
        select(
            IdentityDocumentSecret.found_record_id,
            IdentityDocumentSecret.number_masked,
        ).where(IdentityDocumentSecret.found_record_id.in_(record_ids))
    )
    masked_numbers: dict[UUID, str] = {}
    for record_id, number_masked in identity_rows:
        masked_numbers[record_id] = number_masked

    claim_rows = await session.execute(
        select(
            CandidateMatch.lost_record_id,
            CandidateMatch.found_record_id,
            Claim.id,
            Claim.requester_user_id,
        )
        .join(Claim, Claim.candidate_id == CandidateMatch.id)
        .where(
            (CandidateMatch.lost_record_id.in_(record_ids))
            | (CandidateMatch.found_record_id.in_(record_ids))
        )
        .order_by(Claim.created_at.desc(), Claim.id)
    )
    owners = {record.id: record.owner_user_id for record in records}
    claim_ids: dict[UUID, UUID] = {}
    for lost_id, found_id, claim_id, requester_id in claim_rows:
        for record_id in (lost_id, found_id):
            if record_id in owners and (
                owners[record_id] == actor_id or requester_id == actor_id
            ):
                claim_ids.setdefault(record_id, claim_id)

    return [
        ItemRecordPublic(
            id=record.id,
            owner_user_id=record.owner_user_id,
            kind=record.kind,
            item_type=record.item_type,
            public_category=record.public_category,
            location_area=record.location_area,
            status=record.status,
            name_public=record.name_public,
            description_public=record.description_public,
            event_time_public=record.event_time_public,
            location_public=record.location_public,
            public_image_asset_id=image_ids.get(record.id),
            number_masked=masked_numbers.get(record.id),
            claim_id=claim_ids.get(record.id),
            version=record.version,
            published_at=record.published_at,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
        for record in records
    ]
