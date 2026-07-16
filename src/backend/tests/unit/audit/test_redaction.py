from app.audit.projection import redact_metadata


def test_redaction_recurses_and_removes_sensitive_keys_and_patterns() -> None:
    value = {
        "safe": "published",
        "identity_number": "110101200001010010",
        "nested": {
            "answer_key": "底部有一道裂纹",
            "token": "eyJhbGciOiJIUzI1NiJ9.secret.signature",
            "count": 2,
        },
        "items": [{"phone": "13800138000"}],
    }

    redacted = redact_metadata(value)

    assert redacted["safe"] == "published"
    assert redacted["identity_number"] == "[REDACTED]"
    assert redacted["nested"]["answer_key"] == "[REDACTED]"
    assert redacted["nested"]["token"] == "[REDACTED]"
    assert redacted["nested"]["count"] == 2
    assert redacted["items"][0]["phone"] == "[REDACTED]"


def test_redaction_does_not_mutate_input() -> None:
    original = {"secret": "value", "safe": {"x": 1}}

    redact_metadata(original)

    assert original["secret"] == "value"
