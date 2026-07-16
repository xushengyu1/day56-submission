from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from app.multimodal.schemas import ExtractionDraft, VerificationResult
from app.verification.other import QuestionSetDraft


class ModelAdapterError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class MultimodalPort(Protocol):
    def extract_found_item(
        self, image_ref: str, context: Mapping[str, object]
    ) -> ExtractionDraft: ...

    def generate_questions(self, hidden_description: str) -> QuestionSetDraft: ...

    def verify_answers(
        self, question_set: QuestionSetDraft, answers: Mapping[str, str]
    ) -> VerificationResult: ...
