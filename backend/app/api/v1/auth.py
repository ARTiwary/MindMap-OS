from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import bearer_scheme, get_current_user, rate_limiter
from app.core.security import decode_token
from app.db.database import get_db
from app.db.redis import blacklist_jti
from app.models.user import User
from app.schemas.auth import LogoutRequest, RefreshRequest, TokenPair, UserLogin, UserOut, UserRegister
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Auth endpoints get a lower ceiling than the general API rate limit (applied
# to every route by default via api_router's dependencies) since they're the
# highest-value target for brute-force and credential-stuffing attempts.
strict_limit = rate_limiter(settings.AUTH_RATE_LIMIT_PER_MINUTE)


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(strict_limit)],
)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    user = await auth_service.register_user(db, payload)
    return user


@router.post("/login", response_model=TokenPair, dependencies=[Depends(strict_limit)])
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate_user(db, payload)
    return auth_service.issue_tokens(user)


@router.post("/refresh", response_model=TokenPair, dependencies=[Depends(strict_limit)])
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.refresh_access_token(db, payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: LogoutRequest | None = Body(default=None),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
):
    # Blacklist the access token's jti in Redis until its natural expiry, so
    # a copied/leaked token stops working the instant the user logs out
    # instead of staying valid for the rest of its 15-minute lifetime.
    access_payload = decode_token(credentials.credentials)
    if access_payload and access_payload.get("jti"):
        exp = access_payload.get("exp", 0)
        seconds_left = int(exp - datetime.now(timezone.utc).timestamp())
        await blacklist_jti(access_payload["jti"], seconds_left)

    # If the client also sends its refresh token, revoke that too - otherwise
    # it would remain valid for days and could mint fresh access tokens.
    if payload and payload.refresh_token:
        refresh_payload = decode_token(payload.refresh_token)
        if refresh_payload and refresh_payload.get("jti"):
            exp = refresh_payload.get("exp", 0)
            seconds_left = int(exp - datetime.now(timezone.utc).timestamp())
            await blacklist_jti(refresh_payload["jti"], seconds_left)

    return None


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
