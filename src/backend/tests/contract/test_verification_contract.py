import pytest

from app.db.enums import QuestionResult
from app.multimodal.mock import MockMultimodalAdapter


@pytest.mark.asyncio
async def test_verification_contract_is_conservative_for_match_partial_and_conflict() -> None:
    adapter = MockMultimodalAdapter()
    questions = await adapter.generate_questions("黑色折叠伞，底部有一道裂纹")
    answers = {question.dimension: question.answer_key for question in questions.questions}

    matched = await adapter.verify_answers(questions, answers)
    partial = await adapter.verify_answers(
        questions, {next(iter(answers)): "不确定"}
    )
    conflict = await adapter.verify_answers(
        questions,
        {question.dimension: "完全不同" for question in questions.questions},
    )

    assert matched.result is QuestionResult.MATCH
    assert matched.confidence >= 0.8
    assert partial.result is QuestionResult.UNDETERMINED
    assert partial.confidence < 0.8
    assert conflict.result is QuestionResult.CONFLICT
