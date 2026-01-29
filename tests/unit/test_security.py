from src.core import security


def test_access_token_has_jti_and_type():
    token = security.create_access_token(subject="1", account_id=2)
    payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
    assert payload["type"] == "access"
    assert payload["sub"] == "1"
    assert payload["account_id"] == 2
    assert payload["jti"]


def test_refresh_token_type():
    token = security.create_refresh_token(subject="1")
    payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
    assert payload["type"] == "refresh"
    assert payload["sub"] == "1"
