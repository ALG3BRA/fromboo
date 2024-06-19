import time
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.dals import UserDAL, TokenDAL
from hashing import Hasher
from db.models import User
from typing import Union
from fastapi.security import OAuth2PasswordBearer
from db.session import get_db
import settings
from jose import jwt, JWTError
from fastapi import HTTPException, status

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/token")


async def _get_user_by_email_for_auth(email: str, session: AsyncSession) -> Union[User, None]:
    async with session.begin():
        user_dal = UserDAL(session)
        return await user_dal.get_user_by_email(email=email)


async def _get_user_by_id(user_id, session: AsyncSession) -> Union[User, None]:
    async with session.begin():
        user_dal = UserDAL(session)
        return await user_dal.get_user_by_id(user_id=user_id)


async def authentikate_user(email: str, password: str, session: AsyncSession) -> Union[User, None]:
    user = await _get_user_by_email_for_auth(email, session)
    if not user:
        return
    if not Hasher.verify_password(password, user.hashed_password):
        return
    return user


async def save_refresh_token_to_db(user_id: UUID,
                                   token: UUID,
                                   token_expires: timedelta,
                                   ip_address: str,
                                   session: AsyncSession):
    async with session.begin():
        token_dal = TokenDAL(session)
        await token_dal.save_token(user_id, token, token_expires, ip_address)


async def get_user_by_refresh_token(token: str, session: AsyncSession):
    async with session.begin():
        token_dal = TokenDAL(session)
        token_data = await token_dal.get_token_data(token)
        if not token_data:
            return
        if token_data.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The token's lifetime has expired",
            )
        print(token_data.user_id)
        user_dal = UserDAL(session)
        user = await user_dal.get_user_by_id(user_id=token_data.user_id)
        return user


async def get_current_user_from_token(
        token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = decoded_token.get("sub")
        exp = decoded_token.get("exp")
        if not user_id or exp < time.time():
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await _get_user_by_id(user_id=user_id, session=session)
    if not user:
        raise credentials_exception
    return user

