import pytest

from app.verification.identity import (
    compute_id_hmac,
    mask_cn_id,
    normalize_cn_id,
    validate_cn_id,
)


VALID_ID = "110101200001010010"
VALID_ID_X = "11010120000101007X"


def test_normalize_accepts_nfkc_whitespace_and_lowercase_x() -> None:
    full_width = " １１０１０１２００００１０１００７ｘ "

    assert normalize_cn_id(full_width) == VALID_ID_X


@pytest.mark.parametrize(
    "value",
    [
        VALID_ID[:-1],
        VALID_ID[:-1] + "1",
        "110101200002300010",
        "abcdefghijklmnopqr",
    ],
)
def test_validate_rejects_invalid_length_checksum_date_or_characters(
    value: str,
) -> None:
    assert validate_cn_id(value) is False


def test_validate_accepts_synthetic_valid_ids() -> None:
    assert validate_cn_id(VALID_ID)
    assert validate_cn_id(VALID_ID_X.lower())


def test_mask_keeps_only_first_three_and_last_four_characters() -> None:
    masked = mask_cn_id(VALID_ID)

    assert masked[:3] == VALID_ID[:3]
    assert masked[-4:] == VALID_ID[-4:]
    assert masked[3:-4] == "*" * 11


def test_hmac_is_stable_for_same_input_and_changes_for_input_or_key() -> None:
    first = compute_id_hmac(VALID_ID, b"test-key-v1")

    assert first == compute_id_hmac(VALID_ID, b"test-key-v1")
    assert first != compute_id_hmac(VALID_ID_X, b"test-key-v1")
    assert first != compute_id_hmac(VALID_ID, b"test-key-v2")
    assert len(first) == 64


def test_invalid_input_and_empty_key_do_not_echo_full_identity_number() -> None:
    with pytest.raises(ValueError) as invalid:
        compute_id_hmac("not-an-id", b"test-key-v1")
    with pytest.raises(ValueError) as empty_key:
        compute_id_hmac(VALID_ID, b"")

    assert VALID_ID not in str(invalid.value)
    assert VALID_ID not in str(empty_key.value)
