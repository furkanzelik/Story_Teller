"""Supabase auth for the API (Fase 1 stap 4).

The Flutter client signs in with Supabase and sends the resulting JWT as
`Authorization: Bearer <token>`. We verify it and map it to a local `users` row,
created on first sight.

Supabase projects sign access tokens either
  * asymmetrically (ES256 / RS256) — verified against the project's public
    JWKS at `{supabase_url}/auth/v1/.well-known/jwks.json` (no shared secret), or
  * with a legacy shared HS256 secret (`SUPABASE_JWT_SECRET`).

`verify_supabase_jwt` picks the path from the token's `alg` header, so both
kinds of project work without config changes.
"""

from __future__ import annotations

import logging
import ssl
from dataclasses import dataclass
from functools import lru_cache

import certifi
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models import Subscription, SubscriptionStatus, User

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)

_ASYMMETRIC_ALGS = ["ES256", "RS256", "EdDSA"]


class AuthError(Exception):
    """Raised when a token cannot be trusted."""


@dataclass(frozen=True)
class TokenClaims:
    subject: str  # Supabase user id (uuid as string)
    email: str | None


@lru_cache
def _jwks_client(jwks_url: str) -> jwt.PyJWKClient:
    # PyJWKClient caches fetched keys internally (default lifespan 300s).
    # Explicit CA bundle: the python.org macOS build ships without system
    # roots configured, so urllib's default context fails TLS verification.
    ctx = ssl.create_default_context(cafile=certifi.where())
    return jwt.PyJWKClient(jwks_url, ssl_context=ctx)


def verify_supabase_jwt(
    token: str,
    hs_secret: str | None = None,
    audience: str = "authenticated",
    *,
    jwks_client: jwt.PyJWKClient | None = None,
) -> TokenClaims:
    """Decode + verify a Supabase access token. Raises [AuthError] on any
    problem (bad signature, expired, wrong audience, missing claims)."""
    try:
        alg = jwt.get_unverified_header(token).get("alg", "")
    except jwt.PyJWTError as exc:
        raise AuthError(f"malformed token: {exc}") from exc

    try:
        if alg.startswith("HS"):
            if not hs_secret:
                raise AuthError("HS256 token but no shared secret configured")
            key: object = hs_secret
            algorithms = ["HS256"]
        else:
            if jwks_client is None:
                raise AuthError(f"{alg} token but JWKS verification is not configured")
            key = jwks_client.get_signing_key_from_jwt(token).key
            algorithms = _ASYMMETRIC_ALGS

        payload = jwt.decode(
            token,
            key,
            algorithms=algorithms,
            audience=audience,
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise AuthError(str(exc)) from exc
    except jwt.PyJWKClientError as exc:
        raise AuthError(f"could not fetch signing key: {exc}") from exc

    subject = payload.get("sub")
    if not subject:
        raise AuthError("token has no 'sub' claim")
    return TokenClaims(subject=str(subject), email=payload.get("email"))


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    settings = get_settings()

    if not settings.supabase_url and not settings.supabase_jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth is not configured on the server (SUPABASE_URL / SUPABASE_JWT_SECRET).",
        )
    if creds is None or not creds.credentials:
        logger.warning("auth: no bearer token on request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jwks_client = None
    if settings.supabase_url:
        jwks_client = _jwks_client(
            f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        )

    try:
        claims = verify_supabase_jwt(
            creds.credentials,
            settings.supabase_jwt_secret,
            settings.supabase_jwt_audience,
            jwks_client=jwks_client,
        )
    except AuthError as exc:
        logger.warning("auth: token rejected: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return _upsert_user(db, claims)


def _upsert_user(db: Session, claims: TokenClaims) -> User:
    user = db.scalar(select(User).where(User.auth_subject == claims.subject))
    if user is None:
        user = User(
            email=claims.email or f"{claims.subject}@users.noreply.supabase.co",
            auth_provider="supabase",
            auth_subject=claims.subject,
        )
        db.add(user)
        db.add(
            Subscription(
                user=user,
                status=SubscriptionStatus.free,
                provider="revenuecat",
            )
        )
        db.commit()
        db.refresh(user)
    elif claims.email and user.email != claims.email:
        user.email = claims.email
        db.commit()
    return user
