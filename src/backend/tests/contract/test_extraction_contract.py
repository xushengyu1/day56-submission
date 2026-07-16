from app.db.enums import ExtractionStatus, ItemType
from app.multimodal.mock import MockMultimodalAdapter


def test_extraction_contract_returns_valid_public_draft() -> None:
    draft = MockMultimodalAdapter().extract_found_item(
        "fixture://umbrella.png", {"scenario": "umbrella"}
    )

    assert draft.status is ExtractionStatus.SUCCEEDED
    assert draft.item_type is ItemType.OTHER
    assert draft.name_public
    assert draft.description_public
    assert 0 <= draft.confidence <= 1
    assert draft.provider == "mock"
    assert "110101200001010010" not in str(draft.raw_result_redacted)
