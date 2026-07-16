from __future__ import annotations

from datetime import date
import hashlib
import hmac
import re
import unicodedata


_CHECK_WEIGHTS = (7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2)
_CHECK_CODES = "10X98765432"
_IDENTITY_PATTERN = re.compile(r"^[0-9]{17}[0-9X]$")


def _normalized(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("identity value must be text")
    return "".join(unicodedata.normalize("NFKC", value).split()).upper()


def normalize_cn_id(value: str) -> str:
    normalized = _normalized(value)
    if not validate_cn_id(normalized):
        raise ValueError("invalid identity value")
    return normalized


def validate_cn_id(value: str) -> bool:
    try:
        normalized = _normalized(value)
    except (TypeError, ValueError):
        return False
    if not _IDENTITY_PATTERN.fullmatch(normalized):
        return False
    try:
        date.fromisoformat(
            f"{normalized[6:10]}-{normalized[10:12]}-{normalized[12:14]}"
        )
    except ValueError:
        return False
    checksum = sum(
        int(character) * weight
        for character, weight in zip(normalized[:17], _CHECK_WEIGHTS)
    )
    return normalized[-1] == _CHECK_CODES[checksum % 11]


def compute_id_hmac(normalized: str, key: bytes) -> str:
    if not isinstance(key, bytes) or not key:
        raise ValueError("identity HMAC key must not be empty")
    canonical = normalize_cn_id(normalized)
    return hmac.new(key, canonical.encode("ascii"), hashlib.sha256).hexdigest()


def mask_cn_id(normalized: str) -> str:
    canonical = normalize_cn_id(normalized)
    return canonical[:3] + "*" * 11 + canonical[-4:]
