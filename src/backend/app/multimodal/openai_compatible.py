from __future__ import annotations

from collections.abc import Mapping
import json
import re
import unicodedata

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


def _normalized_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    return re.sub(r"\s+", "", normalized).casefold()


def _string(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError
    return value


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
        question_model: str = "",
        question_base_url: str = "",
        question_api_key: str = "",
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
        # 问题生成专用模型（如 qwen3.7-plus）
        self.question_model = question_model or text_model
        if question_base_url and question_api_key:
            self._question_client = AsyncOpenAI(
                api_key=question_api_key,
                base_url=question_base_url.rstrip("/"),
                timeout=timeout_seconds,
                max_retries=1,
            )
        else:
            self._question_client = self.client

    async def _call_with_client(
        self,
        client: AsyncOpenAI,
        model: str,
        messages: list[ChatCompletionMessageParam],
    ) -> dict[str, object]:
        try:
            completion = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_completion_tokens=1024,
                extra_body={"thinking": {"type": "disabled"}},
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

    async def _call(
        self, model: str, messages: list[ChatCompletionMessageParam]
    ) -> dict[str, object]:
        return await self._call_with_client(self.client, model, messages)

    @staticmethod
    def _float(value: object) -> float:
        if isinstance(value, bool) or not isinstance(value, (str, int, float)):
            raise TypeError
        return float(value)

    async def extract_found_item(
        self, image_data_url: str, context: Mapping[str, object]
    ) -> ExtractionDraft:
        messages: list[ChatCompletionMessageParam] = [
            {
                "role": "system",
                "content": (
                    "你负责分析拾到物品的图片，提取安全的公开描述信息。\n"
                    "\n"
                    "只返回一个 JSON 对象，包含以下字段：\n"
                    "- item_type：物品类型，只能是 IDENTITY_DOCUMENT（身份证明文件）或 OTHER（其他）\n"
                    "- name_public：物品的简短公开名称\n"
                    "- description_public：物品的公开描述\n"
                    "- confidence：置信度，0 到 1 之间的浮点数\n"
                    "\n"
                    "描述时重点关注：\n"
                    "- 颜色（主色调、配色）\n"
                    "- 外观（新旧程度、磨损情况）\n"
                    "- 形状（大小、轮廓、厚薄）\n"
                    "- 材质（皮革、金属、塑料、布料等）\n"
                    "- 品牌标志（如可见）\n"
                    "- 特殊标记（贴纸、划痕、装饰等）\n"
                    "\n"
                    "注意：\n"
                    "- 区分物品主体和背景：只描述物品本身，忽略背景环境（如桌面、地板、墙壁、光线等）\n"
                    "- 背景中的场景信息、环境细节不要写入描述\n"
                    "- 不要暴露完整的身份证明号码\n"
                    "- 不要编造图片中看不到的信息\n"
                    "- description_public 应该简洁明了，便于失主识别"
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
                        "text": "物品上下文信息："
                        + json.dumps(dict(context), ensure_ascii=False),
                    },
                ],
            },
        ]
        parsed = await self._call_with_client(
            self._question_client, self.question_model, messages
        )
        try:
            return ExtractionDraft(
                item_type=ItemType(parsed["item_type"]),
                name_public=_string(parsed["name_public"]),
                description_public=_string(parsed["description_public"]),
                confidence=self._float(parsed["confidence"]),
                provider=self.provider,
                model=self.question_model,
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
                    "你负责针对指定的失物设计物主身份核验问题。\n"
                    "\n"
                    "只返回一个 JSON 对象，其中包含 questions 数组，数组中必须有 2～3 个开放式问题。\n"
                    "\n"
                    "每个问题都必须直接核验 hidden_description（隐藏信息）中明确写出的一项独立事实。\n"
                    "\n"
                    "item_context（物品公开信息）只能用于让问题的措辞更符合当前物品，"
                    "不能询问仅存在于 item_context 中的信息。\n"
                    "\n"
                    "禁止编造或推测隐藏信息中没有提供的：\n"
                    "- 颜色\n"
                    "- 品牌\n"
                    "- 地点\n"
                    "- 标记\n"
                    "- 内部物品\n"
                    "- 用途\n"
                    "- 其他特征\n"
                    "\n"
                    "每个问题必须包含：\n"
                    "- question_text：向认领者展示的问题\n"
                    "- answer_key：用于后端核验的参考答案\n"
                    "\n"
                    "answer_key 必须是 hidden_description 原文中的一段简短、准确的内容。\n"
                    "\n"
                    "question_text 中不能直接出现 answer_key，避免泄露答案。\n"
                    "\n"
                    "每个问题必须对应不同的隐藏特征，不能围绕同一个特征重复提问。\n"
                    "\n"
                    "如果 hidden_description 中不足以提取两个不同的隐藏特征，禁止编造问题。"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {"hidden_description": hidden_description}, ensure_ascii=False
                ),
            },
        ]
        parsed = await self._call_with_client(
            self._question_client, self.question_model, messages
        )
        try:
            raw_questions = parsed["questions"]
            if not isinstance(raw_questions, list):
                raise TypeError
            questions_list: list[QuestionDraft] = []
            for index, item in enumerate(raw_questions):
                if not isinstance(item, Mapping):
                    raise TypeError
                question_text = _string(item["question_text"])
                answer_key = _string(item["answer_key"])
                normalized_answer = _normalized_text(answer_key)
                if normalized_answer and normalized_answer in _normalized_text(
                    question_text
                ):
                    question_text = (
                        f"请描述只有物主知道的第{index + 1}项隐蔽特征。"
                    )
                questions_list.append(
                    QuestionDraft(
                        question_text=question_text,
                        answer_key=answer_key,
                        dimension=f"question_{index + 1}",
                        is_open_ended=True,
                    )
                )
            draft = QuestionSetDraft(questions=tuple(questions_list))
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
                    "or UNDETERMINED. reason_code must be a short code (max 50 chars) "
                    "like: ALL_MATCH, PARTIAL_MATCH, KEY_CONFLICT, ANSWER_VAGUE, "
                    "ANSWER_DETAILED, MINOR_DIFF, MAJOR_DIFF, UNRELATED, MISSING_INFO."
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
                reason_code=_string(parsed["reason_code"]),
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
