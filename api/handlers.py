import uuid
from datetime import datetime
from uuid import UUID

import fastapi
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError

from api.actions.word import WordService
from api.schemas import UserCreate, CustomTranslation
from db.dals import get_user_dal, UserDAL, WordDAL, get_word_dal
from db.db import create_user_in_db
from db.db import users
from db.models import User

from sqlalchemy.ext.asyncio import AsyncSession
from api.actions.auth import get_current_user_from_token
from db.session import get_db, transaction

from api.actions.auth import _get_user_by_email_for_auth
from api.schemas import ShowUser
from hashing import Hasher
from vocabulary_work.service import _get_translated_text

user_router = APIRouter()


@user_router.post("/")
async def create_user(body: UserCreate, user_dal: UserDAL = Depends(get_user_dal)):
    try:
        user = await user_dal.create_user(
            name=body.name,
            email=body.email,
            hashed_password=Hasher.get_password_hash(body.password),
        )
        return ShowUser(
            user_id=user.user_id,
            name=user.name,
            email=user.email,
            is_active=user.is_active,
        )
    except IntegrityError as err:
        raise HTTPException(status_code=503, detail=f"Database error: {err}")


@user_router.get("/get-user")
async def get_user(current_user: User = Depends(get_current_user_from_token)):
    return ShowUser(
        user_id=current_user.user_id,
        name=current_user.name,
        email=current_user.email,
        is_active=current_user.is_active,
    )


@user_router.post("/save-phrase")
async def save_user_phrase(
        word: str,
        word_dal: WordDAL = Depends(get_word_dal),
        current_user: User = Depends(get_current_user_from_token)
):
    try:
        word = word.lower()
        async with word_dal.db_session.begin():
            word_db = await word_dal.create_word(word=word)

            translation = WordService.get_translated_text(word_db.word)
            pos = WordService.get_part_of_speech(translation)

            translation_db = await word_dal.set_translation(
                word_id=word_db.word_id,
                translation=translation,
                pos=pos
            )
            new_user_word = await word_dal.set_bundle_for_user_words(
                user_id=current_user.user_id,
                word_id=word_db.word_id,
                translation_id=translation_db.translation_id,
                time=datetime.utcnow(),
            )
    except IntegrityError:
        await word_dal.db_session.rollback()
    return new_user_word


@user_router.get("/my-words")
async def get_user_words(
        current_user: User = Depends(get_current_user_from_token),
        word_dal: WordDAL = Depends(get_word_dal)):
    try:
        words = await word_dal.get_user_words(current_user.user_id)
        return words
    except IntegrityError as err:
        raise HTTPException(status_code=503, detail=f"Database error: {err}")


@user_router.patch("/set-custom-translation")
async def set_custom_translation(
        data: CustomTranslation,
        word_dal: WordDAL = Depends(get_word_dal),
        current_user: User = Depends(get_current_user_from_token)
):
    if not data.pos:
        data.pos = WordService.get_part_of_speech(data.translation)
    try:
        async with word_dal.db_session.begin():
            translation_db = await word_dal.set_translation(
                data.word_id,
                data.translation,
                data.pos
            )
            await word_dal.delete_user_bundle(current_user.user_id, data.word_id)
            user_word_bundle = await word_dal.set_bundle_for_user_words(
                user_id=current_user.user_id,
                word_id=data.word_id,
                translation_id=translation_db.translation_id,
                time=datetime.utcnow()
            )
            return user_word_bundle
    except IntegrityError as err:
        raise HTTPException(status_code=503, detail=f"Database error: {err}")


@user_router.delete("/delete-word")
async def delete_user_word(
        word_id: UUID,
        word_dal: WordDAL = Depends(get_word_dal),
        current_user: User = Depends(get_current_user_from_token)
):
    try:
        async with word_dal.db_session.begin():
            await word_dal.delete_user_bundle(current_user.user_id, word_id)
            return
    except IntegrityError as err:
        raise HTTPException(status_code=503, detail=f"Database error: {err}")


@user_router.patch("/change-favorite")
async def change_is_favorite_for_word(
        word_id: UUID,
        is_favorite: bool = False,
        word_dal: WordDAL = Depends(get_word_dal),
        current_user: User = Depends(get_current_user_from_token)
):
    try:
        async with word_dal.db_session.begin():
            await word_dal.update_word_favorite(current_user.user_id, word_id, is_favorite)
    except IntegrityError as err:
        raise HTTPException(status_code=503, detail=f"Database error: {err}")
