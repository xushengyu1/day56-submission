import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ClaimStatus
from app.multimodal.mock import MockMultimodalAdapter
from app.multimodal.ports import ModelAdapterError
from app.verification.service import submit_other_claim


class FailingAdapter(MockMultimodalAdapter):
    def verify_answers(self, question_set, answers):
        raise ModelAdapterError("MODEL_UNAVAILABLE")


@pytest.mark.asyncio
async def test_model_failure_routes_claim_to_admin_without_raw_answers(
    other_claim_database,
) -> None:
    engine, ids = other_claim_database
    answers = {question_id: "合成回答" for question_id in ids["question_ids"]}
    async with AsyncSession(engine) as session:
        result = await submit_other_claim(
            session,
            candidate_id=ids["candidate"],
            requester_id=ids["owner"],
            answers=answers,
            adapter=FailingAdapter(),
        )
        await session.commit()

    assert result.status is ClaimStatus.PENDING_ADMIN_REVIEW
    assert result.result_code == "MODEL_UNAVAILABLE"
