import time

import jwt
import pytest

from app.core.security import AuthError, verify_supabase_jwt

SECRET = "test-jwt-secret"
AUD = "authenticated"


def make_token(**overrides) -> str:
    claims = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "parent@example.com",
        "aud": AUD,
        "exp": int(time.time()) + 3600,
    }
    claims.update(overrides)
    return jwt.encode(claims, SECRET, algorithm="HS256")


def test_valid_token_returns_claims():
    claims = verify_supabase_jwt(make_token(), SECRET, AUD)
    assert claims.subject == "11111111-1111-1111-1111-111111111111"
    assert claims.email == "parent@example.com"


def test_expired_token_rejected():
    with pytest.raises(AuthError):
        verify_supabase_jwt(make_token(exp=int(time.time()) - 10), SECRET, AUD)


def test_wrong_audience_rejected():
    with pytest.raises(AuthError):
        verify_supabase_jwt(make_token(aud="other"), SECRET, AUD)


def test_wrong_secret_rejected():
    with pytest.raises(AuthError):
        verify_supabase_jwt(make_token(), "not-the-secret", AUD)


def test_missing_sub_rejected():
    # PyJWT's require=["sub"] fires first, still an AuthError to the caller.
    with pytest.raises(AuthError):
        verify_supabase_jwt(make_token(sub=None), SECRET, AUD)


def test_email_is_optional():
    token = jwt.encode(
        {"sub": "abc", "aud": AUD, "exp": int(time.time()) + 60},
        SECRET,
        algorithm="HS256",
    )
    claims = verify_supabase_jwt(token, SECRET, AUD)
    assert claims.subject == "abc"
    assert claims.email is None
