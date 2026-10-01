import uuid

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token
from app.db.database import get_db
from app.db.redis import check_rate_limit, is_jti_blacklisted
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": {"code": "NOT_AUTHENTICATED", "message": "Valid access token required."}},
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise unauthorized

    jti = payload.get("jti")
    if jti and await is_jti_blacklisted(jti):
        raise unauthorized

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise unauthorized

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise unauthorized

    return user


async def _check_rate_limit(request: Request, *, ceiling: int) -> None:
    """Per-user (if authenticated) or per-IP sliding-window rate limit backed by Redis.

    IMPORTANT: this must never be used directly as `Depends(_check_rate_limit)`
    with a bare `limit: int = ...` parameter. FastAPI resolves plain,
    un-annotated primitive parameters on a dependency as *query parameters*
    of the incoming request - so a route like `/nodes?limit=2` (a normal
    pagination param) would silently overwrite the intended rate-limit
    ceiling with the client-supplied value 2, effectively letting a client
    set their own rate limit (or accidentally rate-limit themselves out).
    Always go through `rate_limiter(ceiling)` below instead, which closes
    over the ceiling so FastAPI never sees it as a request parameter at all.
    """
    auth_header = request.headers.get("authorization", "")
    identifier = auth_header[-24:] if auth_header else (request.client.host if request.client else "anon")
    key = f"ratelimit:{request.url.path}:{identifier}"
    allowed, remaining = await check_rate_limit(key, ceiling)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": {"code": "RATE_LIMITED", "message": "Too many requests. Slow down."}},
        )


def rate_limiter(ceiling: int):
    """Factory that produces a request-only dependency with the ceiling
    baked in via closure, so it never collides with a route's own query
    parameters (see the warning on `_check_rate_limit` above). This is the
    only supported way to apply rate limiting - both the general
    default (see api/v1/__init__.py) and the stricter auth-endpoint limit
    (see api/v1/auth.py) go through this."""

    async def _dependency(request: Request) -> None:
        await _check_rate_limit(request, ceiling=ceiling)

    return _dependency


# The general, default rate limit applied to every route via the API
# router's dependencies list.
rate_limit = rate_limiter(settings.RATE_LIMIT_PER_MINUTE)
