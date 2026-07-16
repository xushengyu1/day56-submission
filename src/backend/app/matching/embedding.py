from __future__ import annotations

import hashlib
import math


def _hash_vector(text: str, dimension: int) -> list[float]:
    if dimension <= 0:
        raise ValueError("EMBEDDING_DIMENSION_INVALID")
    seed = hashlib.sha256(text.encode("utf-8")).digest()
    values = []
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
