from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from typing import Protocol


class EmbeddingError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class EmbeddingPort(Protocol):
    @property
    def model(self) -> str: ...

    @property
    def dimension(self) -> int: ...

    async def embed(self, texts: list[str]) -> list[list[float]]: ...


def _hash_vector(text: str, dimension: int) -> list[float]:
    if dimension <= 0:
        raise ValueError("EMBEDDING_DIMENSION_INVALID")
    seed = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    counter = 0
    while len(values) < dimension:
        block = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
        values.extend(byte / 127.5 - 1 for byte in block)
        counter += 1
    vector = values[:dimension]
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector]


def embed_public_text(texts: list[str], *, dimension: int) -> list[list[float]]:
    return [_hash_vector(text, dimension) for text in texts]


@dataclass(frozen=True)
class HashEmbeddingAdapter:
    dimension: int
    model: str = "mock-hash-v1"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts or any(not text.strip() for text in texts):
            raise EmbeddingError("EMBEDDING_INPUT_INVALID")
        return embed_public_text(texts, dimension=self.dimension)
