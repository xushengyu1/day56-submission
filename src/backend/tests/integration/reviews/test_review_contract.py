import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthorizationError
from app.db.enums import AdminDecision, RecordStatus, ReviewRequestType, UserRole
from app.items.models import ItemRecord
from app.items.service import DomainError
from app.matching.models import CandidateMatch
from app.reviews.models import AdminReview, ClaimAttempt, ReviewRequest
from app.reviews.service import (
    create_claim_review_request,
    create_unmatched_review_request,
    decide_review,
    get_admin_review_detail,
    list_admin_review_queue,
)


@pytest.mark.asyncio
async def test_unmatched_review_can_recommend_or_reject_but_not_approve(
    review_database,
) -> None:
    engine, ids = review_database
    async with AsyncSession(engine, expire_on_commit=False) as session:
        request = await create_unmatched_review_request(
            session,
            lost_record_id=ids["lost"],
            requester_id=ids["owner"],
            reason="没有合适候选",
        )
        await session.flush()
        with pytest.raises(DomainError, match="DECISION_NOT_ALLOWED"):
            await decide_review(
                session,
                review_id=request.id,
                admin_id=ids["admin"],
                decision=AdminDecision.APPROVE_TO_HANDOFF,
                candidate_id=None,
                reason="不应允许",
                idempotency_key="unmatched-invalid",
            )
        first = await decide_review(
            session,
            review_id=request.id,
            admin_id=ids["admin"],
            decision=AdminDecision.RECOMMEND_CANDIDATE,
            candidate_id=ids["candidate"],
            reason="建议核对该候选",
            idempotency_key="unmatched-recommend",
        )
        await session.commit()

    async with AsyncSession(engine) as session:
        second = await decide_review(
            session,
            review_id=request.id,
            admin_id=ids["admin"],
            decision=AdminDecision.RECOMMEND_CANDIDATE,
            candidate_id=ids["candidate"],
            reason="建议核对该候选",
            idempotency_key="unmatched-recommend",
        )
        await session.commit()
        stored = await session.get(ReviewRequest, request.id)
        lost = await session.get(ItemRecord, ids["lost"])
        review_count = await session.scalar(select(func.count(AdminReview.id)))

    assert first == second
    assert first.candidate_id == ids["candidate"]
    assert stored is not None and stored.candidate_snapshot_id == ids["candidate"]
    assert lost is not None and lost.status is RecordStatus.PUBLISHED
    assert review_count == 1


@pytest.mark.asyncio
async def test_claim_review_can_approve_or_reject_but_not_recommend(
    review_database,
) -> None:
    engine, ids = review_database
    async with AsyncSession(engine, expire_on_commit=False) as session:
        request = await create_claim_review_request(
            session,
            claim_id=ids["claim"],
            requester_id=ids["owner"],
            reason="请求人工复核",
        )
        await session.flush()
        with pytest.raises(DomainError, match="DECISION_NOT_ALLOWED"):
            await decide_review(
                session,
                review_id=request.id,
                admin_id=ids["admin"],
                decision=AdminDecision.RECOMMEND_CANDIDATE,
                candidate_id=ids["candidate"],
                reason="不应允许",
                idempotency_key="claim-invalid",
            )
        result = await decide_review(
            session,
            review_id=request.id,
            admin_id=ids["admin"],
            decision=AdminDecision.APPROVE_TO_HANDOFF,
            candidate_id=None,
            reason="证据充分",
            idempotency_key="claim-approve",
        )
        await session.commit()

    assert result.claim_id == ids["claim"]
    assert result.status == "PENDING_HANDOFF"


@pytest.mark.asyncio
async def test_review_queue_and_detail_project_safe_source_specific_context(
    review_database,
) -> None:
    engine, ids = review_database
    async with AsyncSession(engine, expire_on_commit=False) as session:
        unmatched = await create_unmatched_review_request(
            session,
            lost_record_id=ids["lost"],
            requester_id=ids["owner"],
            reason="没有合适候选",
        )
        session.add(
            ClaimAttempt(
                claim_id=ids["claim"],
                user_id=ids["owner"],
                candidate_id=ids["candidate"],
                attempt_no=1,
                submitted_hmac=b"SECRET_SUBMITTED_HMAC",
                result_code="MODEL_UNAVAILABLE",
                answer_summary={"result": "UNDETERMINED"},
            )
        )
        await session.flush()
        queue = await list_admin_review_queue(session, actor_role=UserRole.ADMIN)
        with pytest.raises(AuthorizationError):
            await get_admin_review_detail(
                session,
                review_id=unmatched.id,
                actor_id=ids["owner"],
                actor_role=UserRole.USER,
            )
        claim_detail = await get_admin_review_detail(
            session,
            review_id=ids["claim"],
            actor_id=ids["admin"],
            actor_role=UserRole.ADMIN,
        )
        unmatched_detail = await get_admin_review_detail(
            session,
            review_id=unmatched.id,
            actor_id=ids["admin"],
            actor_role=UserRole.ADMIN,
        )

    assert {item.source for item in queue} >= {
        "CLAIM",
        ReviewRequestType.UNMATCHED.value,
    }
    assert claim_detail.candidate is not None
    assert claim_detail.candidates == []
    assert claim_detail.evidence[0].result_code == "MODEL_UNAVAILABLE"
    assert unmatched_detail.lost_record is not None
    assert [candidate.id for candidate in unmatched_detail.candidates] == [
        ids["candidate"]
    ]
    assert unmatched_detail.candidates[0].found_record.id == ids["found"]
    serialized = str(
        [claim_detail.model_dump(mode="json"), unmatched_detail.model_dump(mode="json")]
    ).casefold()
    for forbidden in ("submitted_hmac", "secret_submitted_hmac", "answer_key", "object_key"):
        assert forbidden not in serialized


@pytest.mark.asyncio
async def test_unmatched_review_rejects_unrelated_or_stale_candidates(
    review_database,
) -> None:
    engine, ids = review_database
    async with AsyncSession(engine, expire_on_commit=False) as session:
        request = await create_unmatched_review_request(
            session,
            lost_record_id=ids["lost"],
            requester_id=ids["owner"],
            reason="没有合适候选",
        )
        fixture_lost = await session.get(ItemRecord, ids["lost"])
        assert fixture_lost is not None
        unrelated_lost = ItemRecord(
            owner_user_id=ids["owner"],
            kind=fixture_lost.kind,
            item_type=fixture_lost.item_type,
            public_category=fixture_lost.public_category,
            location_area=fixture_lost.location_area,
            status=RecordStatus.PUBLISHED,
            name_public="另一把伞",
        )
        session.add(unrelated_lost)
        await session.flush()
        unrelated_candidate = CandidateMatch(
            lost_record_id=unrelated_lost.id,
            found_record_id=ids["found"],
            semantic_score=40,
            time_score=20,
            location_score=20,
            completeness_score=10,
            total_score=90,
            reason_codes=[],
            conflict_codes=[],
            rule_version="v1",
            model_version="mock",
        )
        session.add(unrelated_candidate)
        await session.flush()

        with pytest.raises(DomainError, match="CANDIDATE_INVALID"):
            await decide_review(
                session,
                review_id=request.id,
                admin_id=ids["admin"],
                decision=AdminDecision.RECOMMEND_CANDIDATE,
                candidate_id=unrelated_candidate.id,
                reason="错误候选",
                idempotency_key="unmatched-unrelated",
            )

        found = await session.get(ItemRecord, ids["found"])
        assert found is not None
        found.status = RecordStatus.CLAIMED
        await session.flush()
        detail = await get_admin_review_detail(
            session,
            review_id=request.id,
            actor_id=ids["admin"],
            actor_role=UserRole.ADMIN,
        )
        assert detail.candidates == []
        with pytest.raises(DomainError, match="CANDIDATE_INVALID"):
            await decide_review(
                session,
                review_id=request.id,
                admin_id=ids["admin"],
                decision=AdminDecision.RECOMMEND_CANDIDATE,
                candidate_id=ids["candidate"],
                reason="候选已失效",
                idempotency_key="unmatched-stale",
            )
