import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ClaimStatus
from app.multimodal.mock import MockMultimodalAdapter
from app.verification.service import submit_other_claim


@pytest.mark.asyncio
async def test_all_matching_answers_handoff_and_unclear_answers_review(
    other_claim_database,
) -> None:
    engine, ids = other_claim_database
    answers = {
        ids["question_ids"][0]: "一道细小裂纹",
        ids["question_ids"][1]: "字母A",
    }
    async with AsyncSession(engine) as session:
        matched = await submit_other_claim(
            session,
            candidate_id=ids["candidate"],
            requester_id=ids["owner"],
            answers=answers,
            adapter=MockMultimodalAdapter(),
        )
        await session.commit()

    assert matched.status is ClaimStatus.PENDING_HANDOFF
    assert matched.result_code == "ANSWERS_VERIFIED"
