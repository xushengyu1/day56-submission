from __future__ import annotations

import asyncio
from collections.abc import Mapping
from http import HTTPStatus
import math

import dashscope  # type: ignore[import-untyped]

from app.matching.embedding import EmbeddingError


class DashScopeEmbeddingAdapter:
    def __init__(
        self,
        *,
        model: str,
        dimension: int,
        api_key: str,
        base_url: str | None = None,
    ) -> None:
        self.model = model
        self.dimension = dimension
        self._api_key = api_key
        self._base_url = base_url

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if (
            not texts
            or len(texts) > 20
            or any(not isinstance(text, str) or not text.strip() for text in texts)
        ):
            raise EmbeddingError("EMBEDDING_INPUT_INVALID")
        try:
            if self._base_url:
                dashscope.base_http_api_url = self._base_url.rstrip("/")
            response = await asyncio.to_thread(
                dashscope.TextEmbedding.call,
                model=self.model,
                input=texts,
                dimension=self.dimension,
                api_key=self._api_key,
            )
            return self._parse_response(response, len(texts))
        except EmbeddingError:
            raise
        except Exception:
            raise EmbeddingError("EMBEDDING_UNAVAILABLE") from None

    def _parse_response(
        self, response: object, expected_count: int
    ) -> list[list[float]]:
        if getattr(response, "status_code", None) != HTTPStatus.OK:
            raise EmbeddingError("EMBEDDING_UNAVAILABLE")
        output = getattr(response, "output", None)
        if not isinstance(output, Mapping):
            raise EmbeddingError("EMBEDDING_UNAVAILABLE")
        raw_embeddings = output.get("embeddings")
        if not isinstance(raw_embeddings, list) or len(raw_embeddings) != expected_count:
            raise EmbeddingError("EMBEDDING_UNAVAILABLE")

        ordered: list[list[float] | None] = [None] * expected_count
        for item in raw_embeddings:
            if not isinstance(item, Mapping):
                raise EmbeddingError("EMBEDDING_UNAVAILABLE")
            index = item.get("text_index")
            values = item.get("embedding")
            if (
                not isinstance(index, int)
                or isinstance(index, bool)
                or not 0 <= index < expected_count
                or ordered[index] is not None
                or not isinstance(values, list)
                or len(values) != self.dimension
            ):
                raise EmbeddingError("EMBEDDING_UNAVAILABLE")
            vector: list[float] = []
            for value in values:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise EmbeddingError("EMBEDDING_UNAVAILABLE")
                number = float(value)
                if not math.isfinite(number):
                    raise EmbeddingError("EMBEDDING_UNAVAILABLE")
                vector.append(number)
            ordered[index] = vector

        if any(vector is None for vector in ordered):
            raise EmbeddingError("EMBEDDING_UNAVAILABLE")
        return [vector for vector in ordered if vector is not None]
