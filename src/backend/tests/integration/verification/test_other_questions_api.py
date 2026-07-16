import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.verification.service import get_other_questions


@pytest.mark.asyncio
async def test_other_questions_projection_never_returns_answers(other_claim_database) -> None:
    engine, ids = other_claim_database
    async with AsyncSession(engine) as session:
        questions = await get_other_questions(
            session, candidate_id=ids["candidate"], requester_id=ids["owner"]
        )

    body = [question.model_dump(mode="json") for question in questions]
    assert len(body) == 2
    assert "answer_key" not in str(body)
    assert "hidden_description" not in str(body)
