import pytest

from app.api.deps import extract_bearer_token
from app.auth.security import AuthenticationError


def test_extract_bearer_token_accepts_only_bearer_scheme() -> None:
    assert extract_bearer_token("Bearer abc.def.ghi") == "abc.def.ghi"
    with pytest.raises(AuthenticationError, match="UNAUTHENTICATED"):
        extract_bearer_token(None)
    with pytest.raises(AuthenticationError, match="INVALID_TOKEN"):
        extract_bearer_token("Basic abc")
