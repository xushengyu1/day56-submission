from __future__ import annotations

from collections.abc import Mapping
import json
import re

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    RateLimitError,
)
from openai.types.chat import ChatCompletionMessageParam
from pydantic import ValidationError

from app.db.enums import ExtractionStatus, ItemType, QuestionResult
from app.multimodal.ports import ModelAdapterError
from app.multimodal.schemas import ExtractionDraft, VerificationResult
from app.verification.other import (
    QuestionDraft,
    QuestionSetDraft,
    validate_question_set,
)


_JSON_FENCE = re.compile(
    r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.IGNORECASE | re.DOTALL
)


def _json_object(content: str) -> dict[str, object]:
    match = _JSON_FENCE.match(content)
    payload = match.group(1) if match else content
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise TypeError
    return parsed


class OpenAICompatibleAdapter:
    provider = "xiaomi-mimo"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        multimodal_model: str,
        text_model: str,
        version: str,
        client: AsyncOpenAI | None = None,
        timeout_seconds: float = 20,
    ) -> None:
        self.multimodal_model = multimodal_model
        self.text_model = text_model
        self.model = text_model
        self.version = version
        self.client = client or AsyncOpenAI(
            api_key=api_key,
            base_url=base_url.rstrip("/"),
            timeout=timeout_seconds,
            max_retries=1,
        )

    async def _call(
        self, model: str, messages: list[ChatCompletionMessageParam]
    ) -> dict[str, object]:
        try:
            completion = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_completion_tokens=1024,
            )
        except (APITimeoutError, APIConnectionError, RateLimitError):
            raise ModelAdapterError("MODEL_UNAVAILABLE") from None
        except APIStatusError as error:
            code = (
                "MODEL_UNAVAILABLE"
                if error.status_code >= 500
                else "MODEL_HTTP_ERROR"
            )
            raise ModelAdapterError(code) from None

        try:
            content = completion.choices[0].message.content
            if not isinstance(content, str) or not content.strip():
                raise TypeError
            return _json_object(content)
        except (ValueError, TypeError, IndexError, AttributeError):
            raise ModelAdapterError("MODEL_RESPONSE_INVALID") from None

    @staticmethod
    def _float(value: object) -> float:
        if not isinstance(value, (str, int, float)):
            raise TypeError
        return float(value)

    async def extract_found_item(
        self, image_data_url: str, context: Mapping[str, object]
    ) -> ExtractionDraft:
        messages: list[ChatCompletionMessageParam] = [
            {
                "role": "system",
                "content": (
                    "You are Xiaomi MiMo. Extract a safe public lost-item draft. "
                    "Return only one JSON object with item_type, name_public, "
                    "description_public, and confidence. item_type must be "
                    "IDENTITY_DOCUMENT or OTHER, and confidence must be between "
                    "0 and 1. Do not reveal full identity numbers."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_url},
                    },
                    {
                        "type": "text",
                        "text": "Context: "
                        + json.dumps(dict(context), ensure_ascii=False),
                    },
                ],
            },
        ]
        parsed = await self._call(self.multimodal_model, messages)
        try:
            return ExtractionDraft(
                item_type=ItemType(parsed["item_type"]),
                name_public=str(parsed["name_public"]),
                description_public=str(parsed["description_public"]),
                confidence=self._float(parsed["confidence"]),
                provider=self.provider,
                model=self.multimodal_model,
                version=self.version,
                status=ExtractionStatus.SUCCEEDED,
                raw_result_redacted={"response_valid": True},
            )
        except (KeyError, TypeError, ValueError, ValidationError):
            raise ModelAdapterError("MODEL_RESPONSE_INVALID") from None

    async def generate_questions(self, hidden_description: str) -> QuestionSetDraft:
        messages: list[ChatCompletionMessageParam] = [
            {
                "role": "system",
                "content": (
                    "You are Xiaomi MiMo. Return only one JSON object with a "
                    "questions array containing 2 or 3 open-ended ownership-"
                    "verification questions. Each item must contain question_text, "
                    "answer_key, dimension, and is_open_ended. Never include an "
                    "answer in its question text."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {"hidden_description": hidden_description}, ensure_ascii=False
                ),
            },
        ]
        parsed = await self._call(self.text_model, messages)
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

    async def verify_answers(
        self, question_set: QuestionSetDraft, answers: Mapping[str, str]
    ) -> VerificationResult:
        verification_payload = {
            "questions": [
                {
                    "dimension": question.dimension,
                    "question": question.question_text,
                    "answer_key": question.answer_key,
                    "claimant_answer": answers.get(question.dimension, ""),
                }
                for question in question_set.questions
            ]
        }
        messages: list[ChatCompletionMessageParam] = [
            {
                "role": "system",
                "content": (
                    "You are Xiaomi MiMo. Compare claimant answers with reference "
                    "answers. Return only one JSON object with result, confidence, "
                    "and reason_code. result must be MATCH, PARTIAL_MATCH, CONFLICT, "
                    "or UNDETERMINED."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(verification_payload, ensure_ascii=False),
            },
        ]
        parsed = await self._call(self.text_model, messages)
        try:
            result = VerificationResult(
                result=QuestionResult(parsed["result"]),
                confidence=self._float(parsed["confidence"]),
                reason_code=str(parsed["reason_code"]),
                provider=self.provider,
                model=self.text_model,
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
