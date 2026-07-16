from app.verification.other import (
    QuestionDraft,
    QuestionSetDraft,
    validate_question_set,
)


def _valid_draft() -> QuestionSetDraft:
    return QuestionSetDraft(
        questions=(
            QuestionDraft(
                question_text="请描述伞柄底部的细节。",
                answer_key="底部有一道裂纹",
                dimension="shape",
            ),
            QuestionDraft(
                question_text="请描述伞套内侧的标记。",
                answer_key="有字母标记",
                dimension="mark",
            ),
        ),
        public_description="黑色折叠伞",
    )


def test_two_or_three_open_questions_are_valid() -> None:
    result = validate_question_set(_valid_draft())

    assert result.valid
    assert result.errors == ()


def test_question_count_must_be_between_two_and_three() -> None:
    one = _valid_draft()
    four = QuestionSetDraft(
        questions=one.questions + (
            QuestionDraft("请描述第三个细节。", "第三个细节", "third"),
            QuestionDraft("请描述第四个细节。", "第四个细节", "fourth"),
        )
    )

    assert "QUESTION_COUNT" in validate_question_set(
        QuestionSetDraft(questions=one.questions[:1])
    ).errors
    assert "QUESTION_COUNT" in validate_question_set(four).errors


def test_questions_must_be_open_ended_and_dimensions_unique() -> None:
    draft = QuestionSetDraft(
        questions=(
            QuestionDraft("请选择颜色。", "黑色", "color", is_open_ended=False),
            QuestionDraft("请描述颜色的其他细节。", "黑色", "color"),
        )
    )

    result = validate_question_set(draft)

    assert "NOT_OPEN_ENDED" in result.errors
    assert "DUPLICATE_DIMENSION" in result.errors


def test_question_cannot_contain_answer_text() -> None:
    draft = QuestionSetDraft(
        questions=(
            QuestionDraft("请回答：底部有一道裂纹。", "底部有一道裂纹", "shape"),
            QuestionDraft("请描述伞套。", "有字母标记", "mark"),
        )
    )

    result = validate_question_set(draft)

    assert result.valid is False
    assert "ANSWER_LEAKAGE" in result.errors


def test_public_description_cannot_contain_answer_text() -> None:
    draft = QuestionSetDraft(
        questions=(
            QuestionDraft("请描述伞柄细节。", "底部有一道裂纹", "shape"),
            QuestionDraft("请描述伞套标记。", "有字母标记", "mark"),
        ),
        public_description="黑色折叠伞，底部有一道裂纹",
    )

    result = validate_question_set(draft)

    assert result.valid is False
    assert result.errors == ("ANSWER_LEAKAGE",)
