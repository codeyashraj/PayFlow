from uuid import uuid4
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


def test_password_hash_and_verify():
    hashed = hash_password("correct-password")
    assert hashed != "correct-password"
    assert verify_password("correct-password", hashed)
    assert not verify_password("wrong-password", hashed)


def test_jwt_round_trip():
    user_id = uuid4()
    assert decode_access_token(create_access_token(user_id)) == user_id
