from app.multimodal.mock import MockMultimodalAdapter
from app.verification.other import validate_question_set


def test_question_contract_is_compatible_with_t02_validation() -> None:
    questions = MockMultimodalAdapter().generate_questions("黑色折叠伞，底部有一道裂纹")

    validation = validate_question_set(questions)

    assert validation.valid
    assert 2 <= len(questions.questions) <= 3
    assert all(question.is_open_ended for question in questions.questions)
