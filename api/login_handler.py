import uuid
from datetime import timedelta, datetime, timezone

from fastapi import APIRouter, HTTPException, status, Response, Request, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

import settings
from api.actions.auth import authentikate_user, save_refresh_token_to_db, get_user_by_refresh_token
from db.session import get_db
from api.schemas import Token
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends
from security import create_access_token

login_router = APIRouter()


@login_router.post("/token", response_model=Token)
async def login_for_access_token(
        request: Request,
        response: Response,
        form_data: OAuth2PasswordRequestForm = Depends(),
        session: AsyncSession = Depends(get_db)
):
    user = await authentikate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.user_id)},
        expires_delta=access_token_expires,
    )

    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = uuid.uuid4()  # заменить
    ip_address = request.client.host
    await save_refresh_token_to_db(user.user_id, refresh_token, refresh_token_expires, ip_address, session)

    response.set_cookie(
        key="refresh_token",
        value=str(refresh_token),
        expires=datetime.now(timezone.utc) + refresh_token_expires,
        httponly=True,
    )

    print(response.raw_headers)

    access_token_expires_at = access_token_expires + datetime.utcnow()
    return {"access_token": access_token, "exp": access_token_expires_at, "token_type": "bearer"}


@login_router.post("/refresh", response_model=Token)
async def to_refresh_token(
        request: Request,
        response: Response,
        refresh_token: str = Cookie(None),
        session: AsyncSession = Depends(get_db),
):
    if refresh_token:
        print("___ref tok: " + refresh_token)
    if not refresh_token:
        print("__no refresh_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизован",
        )

    user = await get_user_by_refresh_token(refresh_token, session)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized user",
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.user_id)},
        expires_delta=access_token_expires,
    )

    new_refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = uuid.uuid4()  # заменить
    ip_address = request.client.host
    await save_refresh_token_to_db(user.user_id, new_refresh_token, new_refresh_token_expires, ip_address, session)

    response.set_cookie(
        key="refresh_token",
        value=str(new_refresh_token),
        expires=datetime.now(timezone.utc) + new_refresh_token_expires,
        httponly=True,
    )

    access_token_expires_at = access_token_expires + datetime.utcnow()

    return {"access_token": access_token, "exp": access_token_expires_at, "token_type": "bearer", "ip": str(ip_address)}

