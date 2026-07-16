from app.matching.embedding import embed_public_text


def test_embedding_contract_is_deterministic_and_dimension_locked() -> None:
    first = embed_public_text(["黑色折叠伞", "蓝色耳机"], dimension=8)
    second = embed_public_text(["黑色折叠伞", "蓝色耳机"], dimension=8)

    assert first == second
    assert len(first) == 2
    assert all(len(vector) == 8 for vector in first)
    assert all(abs(sum(value * value for value in vector) - 1) < 1e-6 for vector in first)
