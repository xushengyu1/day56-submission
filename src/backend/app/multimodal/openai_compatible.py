from __future__ import annotations

from collections.abc import Mapping
import json

import httpx
from pydantic import ValidationError

from app.db.enums import ExtractionStatus, ItemType, QuestionResult
from app.multimodal.ports import ModelAdapterError
from app.multimodal.schemas import ExtractionDraft, VerificationResult
from app.verification.other import (
    QuestionDraft,
    QuestionSetDraft,
    validate_question_set,
)


class OpenAICompatibleAdapter:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        version: str,
        client: httpx.Client | None = None,
        timeout_seconds: float = 20,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.version = version
        self.client = client or httpx.Client(timeout=timeout_seconds)

    def _call(self, operation: str, payload: Mapping[str, object]) -> dict[str, object]:
        response: httpx.Response | None = None
        for attempt in range(2):
            try:
                response = self.client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model, "operation": operation, "input": payload},
                )
            except (httpx.TimeoutException, httpx.TransportError):
                if attempt == 0:
                    continue
                raise ModelAdapterError("MODEL_UNAVAILABLE") from None
            if response.status_code == 429 or response.status_code >= 500:
                if attempt == 0:
                    continue
                raise ModelAdapterError("MODEL_UNAVAILABLE")
            if response.status_code >= 400:
                raise ModelAdapterError("MODEL_HTTP_ERROR")
            break

        if response is None:
            raise ModelAdapterError("MODEL_UNAVAILABLE")
        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            parsed = json.loads(content) if isinstance(content, str) else content
            if not isinstance(parsed, dict):
                raise TypeError
            return parsed
        except (ValueError, TypeError, KeyError, IndexError, AttributeError):
            raise ModelAdapterError("MODEL_RESPONSE_INVALID") from None

    @staticmethod
    def _float(value: object) -> float:
        if not isinstance(value, (str, int, float)):
            raise TypeError
        return float(value)

    def extract_found_item(
        self, image_ref: str, context: Mapping[str, object]
    ) -> ExtractionDraft:
        parsed = self._call(
            "extract_found_item", {"image_ref": image_ref, "context": dict(context)}
        )
        try:
            return ExtractionDraft(
                item_type=ItemType(parsed["item_type"]),
                name_public=str(parsed["name_public"]),
                description_public=str(parsed["description_public"]),
                confidence=self._float(parsed["confidence"]),
                provider="openai-compatible",
                model=self.model,
                version=self.version,
                status=ExtractionStatus.SUCCEEDED,
                raw_result_redacted={"response_valid": True},
            )
        except (KeyError, TypeError, ValueError, ValidationError):
            raise ModelAdapterError("MODEL_RESPONSE_INVALID") from None

    def generate_questions(self, hidden_description: str) -> QuestionSetDraft:
        parsed = self._call(
            "generate_questions", {"hidden_description": hidden_description}
        )
        try:
            raw_questions = parsed["questions"]
            if not isinstance(raw_questions, list):
                raise TypeError
            questions = tuple(
                QuestionDraft(
                    question_text=str(item["question_text"]),
                    answer_key=str(item["answer_key"]),
                    dimension=str(item["dimension"]),
                    is_open_ended=bool(item.get("is_open_ended", True)),
                )
                for item in raw_questions
                if isinstance(item, Mapping)
            )
            if len(questions) != len(raw_questions):
                raise TypeError
            draft = QuestionSetDraft(questions=questions)
        except (KeyError, TypeError, ValueError):
            raise ModelAdapterError("MODEL_RESPONSE_INVALID") from None
        if not validate_question_set(draft).valid:
            raise ModelAdapterError("MODEL_RESPONSE_INVALID")
        return draft

    def verify_answers(
        self, question_set: QuestionSetDraft, answers: Mapping[str, str]
    ) -> VerificationResult:
        parsed = self._call(
            "verify_answers",
            {
                "questions": [
                    {"dimension": question.dimension, "question": question.question_text}
                    for question in question_set.questions
                ],
                "answers": dict(answers),
            },
        )
        try:
            result = VerificationResult(
                result=QuestionResult(parsed["result"]),
                confidence=self._float(parsed["confidence"]),
                reason_code=str(parsed["reason_code"]),
                provider="openai-compatible",
                model=self.model,
                version=self.version,
            )
        except (KeyError, TypeError, ValueError, ValidationError):
            raise ModelAdapterError("MODEL_RESPONSE_INVALID") from None
        if result.result is QuestionResult.MATCH and result.confidence < 0.8:
            return result.model_copy(
                update={
                    "result": QuestionResult.UNDETERMINED,
                    "reason_code": "CONFIDENCE_TOO_LOW",
                }
            )
        return result
