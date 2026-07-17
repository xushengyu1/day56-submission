from __future__ import annotations

from collections.abc import Mapping
import re
import unicodedata

from app.db.enums import ExtractionStatus, ItemType, QuestionResult
from app.multimodal.schemas import ExtractionDraft, VerificationResult
from app.verification.other import QuestionDraft, QuestionSetDraft


def _normalized(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value)).casefold()


class MockMultimodalAdapter:
    provider = "mock"
    model = "deterministic-fixtures"
    version = "fixture-v1"

    async def extract_found_item(
        self, image_data_url: str, context: Mapping[str, object]
    ) -> ExtractionDraft:
        scenario = str(context.get("scenario", "umbrella"))
        if scenario != "umbrella":
            raise ValueError("MOCK_SCENARIO_UNKNOWN")
        return ExtractionDraft(
            item_type=ItemType.OTHER,
            name_public="黑色折叠伞",
            description_public="一把黑色折叠伞，外观完整。",
            confidence=0.93,
            provider=self.provider,
            model=self.model,
            version=self.version,
            status=ExtractionStatus.SUCCEEDED,
            raw_result_redacted={"scenario": scenario, "image_ref": "[REDACTED]"},
        )

    async def generate_questions(self, hidden_description: str) -> QuestionSetDraft:
        if not hidden_description.strip():
            raise ValueError("HIDDEN_INFO_INSUFFICIENT")
        return QuestionSetDraft(
            questions=(
                QuestionDraft(
                    question_text="请描述伞柄底部可识别的细节。",
                    answer_key="一道细小裂纹",
                    dimension="handle_detail",
                ),
                QuestionDraft(
                    question_text="请描述伞套内侧的标记。",
                    answer_key="字母A",
                    dimension="inner_mark",
                ),
            )
        )

    async def verify_answers(
        self, question_set: QuestionSetDraft, answers: Mapping[str, str]
    ) -> VerificationResult:
        compared = []
        for question in question_set.questions:
            answer = answers.get(question.dimension)
            if answer is None or _normalized(answer) in {"", "不确定", "不知道"}:
                return self._result(QuestionResult.UNDETERMINED, 0.5, "ANSWER_UNCLEAR")
            compared.append(_normalized(answer) == _normalized(question.answer_key))
        if all(compared):
            return self._result(QuestionResult.MATCH, 0.95, "ALL_KEY_ANSWERS_MATCH")
        if any(compared):
            return self._result(QuestionResult.PARTIAL_MATCH, 0.7, "PARTIAL_MATCH")
        return self._result(QuestionResult.CONFLICT, 0.9, "KEY_ANSWER_CONFLICT")

    def _result(
        self, result: QuestionResult, confidence: float, reason_code: str
    ) -> VerificationResult:
        return VerificationResult(
            result=result,
            confidence=confidence,
            reason_code=reason_code,
            provider=self.provider,
            model=self.model,
            version=self.version,
        )
