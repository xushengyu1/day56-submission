from dataclasses import dataclass
import re
import unicodedata


def _normalize(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value)).casefold()


@dataclass(frozen=True)
class QuestionDraft:
    question_text: str
    answer_key: str
    dimension: str
    is_open_ended: bool = True


@dataclass(frozen=True)
class QuestionSetDraft:
    questions: tuple[QuestionDraft, ...]
    public_description: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "questions", tuple(self.questions))


@dataclass(frozen=True)
class QuestionSetValidation:
    valid: bool
    errors: tuple[str, ...]


def validate_question_set(draft: QuestionSetDraft) -> QuestionSetValidation:
    errors: list[str] = []
    questions = draft.questions
    if not 2 <= len(questions) <= 3:
        errors.append("QUESTION_COUNT")

    dimensions: set[str] = set()
    public_description = _normalize(draft.public_description)
    for question in questions:
        if not question.is_open_ended:
            errors.append("NOT_OPEN_ENDED")
        if not question.question_text.strip() or not question.answer_key.strip():
            errors.append("EMPTY_TEXT")

        dimension = _normalize(question.dimension)
        if dimension in dimensions:
            errors.append("DUPLICATE_DIMENSION")
        dimensions.add(dimension)

        question_text = _normalize(question.question_text)
        answer_key = _normalize(question.answer_key)
        if answer_key and answer_key in question_text:
            errors.append("ANSWER_LEAKAGE")
        if answer_key and answer_key in public_description:
            errors.append("ANSWER_LEAKAGE")

    unique_errors = tuple(dict.fromkeys(errors))
    return QuestionSetValidation(valid=not unique_errors, errors=unique_errors)
