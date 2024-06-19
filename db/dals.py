from datetime import datetime, timedelta
from typing import Union, AsyncGenerator
from uuid import UUID

from fastapi import Depends
from sqlalchemy import and_
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import exists

from db.models import User, WordBase, Translation, UserWords, RefreshToken
from db.session import get_db


###########################################################
# BLOCK FOR INTERACTION WITH DATABASE IN BUSINESS CONTEXT #
###########################################################


class UserDAL:
    """Data Access Layer for operating user info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_user(
            self,
            name: str,
            email: str,
            hashed_password: str,
    ) -> User:
        new_user = User(
            name=name,
            email=email,
            hashed_password=hashed_password,
        )
        self.db_session.add(new_user)
        await self.db_session.flush()
        return new_user

    async def get_user_by_email(
            self,
            email
    ) -> User:
        query = select(User).where(email == User.email)
        res = await self.db_session.execute(query)
        user_row = res.fetchone()
        if user_row is not None:
            return user_row[0]

    async def get_user_by_id(
            self,
            user_id
    ) -> User:
        query = select(User).where(user_id == User.user_id)
        res = await self.db_session.execute(query)
        user_row = res.fetchone()
        if user_row is not None:
            return user_row[0]


async def get_user_dal(db_session: AsyncSession = Depends(get_db)) -> AsyncGenerator[UserDAL, None]:
    yield UserDAL(db_session)


class WordDAL:
    """Data Access Layer for operating words"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_word(self, word: str) -> WordBase:
        new_word = await self.get_word_in_word_db(word)
        if not new_word:
            new_word = WordBase(word=word)
            self.db_session.add(new_word)
            await self.db_session.flush()
        return new_word

    async def get_word_in_word_db(self, word: str) -> Union[WordBase, None]:
        query = select(WordBase).where(WordBase.word == word)
        result = await self.db_session.execute(query)
        word_row = result.fetchone()
        if word_row:
            return word_row[0]

    async def translation_exists(self, word_id: UUID, translation: str) -> Union[Translation, None]:
        stmt = select(Translation).filter_by(word_id=word_id, translation=translation)
        result = await self.db_session.execute(stmt)
        return result.scalars().first()

    async def set_translation(self,
                              word_id: UUID,
                              translation: str,
                              pos: str
                              ) -> Union[Translation, None]:
        existing_translation = await self.translation_exists(word_id, translation)
        if existing_translation:
            return existing_translation

        new_translation = Translation(
            word_id=word_id,
            translation=translation,
            pos=pos
        )
        self.db_session.add(new_translation)
        try:
            await self.db_session.flush()
            return new_translation
        except IntegrityError:
            await self.db_session.rollback()

    async def get_user_words(self, user_id):
        Word = aliased(WordBase)
        TranslationAlias = aliased(Translation)

        stmt = (
            select(
                UserWords,
                Word.word_id,
                Word.word,
                TranslationAlias.pos,
                TranslationAlias.translation
            )
            .filter(UserWords.user_id == user_id)
            .join(Word, UserWords.word_id == Word.word_id)
            .join(TranslationAlias, UserWords.translation_id == TranslationAlias.translation_id)
        )
        result = await self.db_session.execute(stmt)
        return [
            {
                "word_id": row.word_id,
                "word": row.word,
                "translation": row.translation,
                "part_of_speech": row.pos,
                "added_at": row.UserWords.added_at,
                "is_favorite": row.UserWords.is_favorite
            }
            for row in result.fetchall()
        ]

    async def set_bundle_for_user_words(self,
                                        user_id: UUID,
                                        word_id: UUID,
                                        translation_id: UUID,
                                        time: datetime
                                        ) -> Union[UserWords, None]:
        new_bundle = UserWords(
            user_id=user_id,
            word_id=word_id,
            translation_id=translation_id,
            added_at=time
        )
        self.db_session.add(new_bundle)
        try:
            await self.db_session.flush()
        except IntegrityError:
            ...
        return new_bundle

    async def delete_user_bundle(self, user_id: UUID, word_id: UUID):
        stmt = select(UserWords).filter_by(user_id=user_id, word_id=word_id)
        result = await self.db_session.execute(stmt)
        bundle = result.scalars().first()

        if bundle:
            await self.db_session.delete(bundle)
            await self.db_session.flush()
            return True
        return False


async def get_word_dal(db_session: AsyncSession = Depends(get_db)) -> AsyncGenerator[WordDAL, None]:
    yield WordDAL(db_session)


class TokenDAL:

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def save_token(self, user_id: UUID, token: UUID, token_expires: timedelta, ip_address: str) -> Union[RefreshToken, None]:
        try:
            expires_at = datetime.utcnow() + token_expires

            # Попытка обновить существующую запись
            stmt = (
                update(RefreshToken)
                .where(RefreshToken.user_id == user_id)
                .values(
                    token=token,
                    expires_at=expires_at,
                    ip_address=ip_address,
                    registered_at=datetime.utcnow()
                )
                .returning(RefreshToken)
            )

            result = await self.db_session.execute(stmt)
            updated_token = result.scalar_one_or_none()

            # Если обновление не произошло, создаём новую запись
            if updated_token is None:
                new_token_data = RefreshToken(
                    token=token,
                    user_id=user_id,
                    expires_at=expires_at,
                    ip_address=ip_address
                )
                self.db_session.add(new_token_data)
                await self.db_session.flush()
                await self.db_session.commit()
                return new_token_data

            await self.db_session.commit()
            return updated_token

        except IntegrityError:
            await self.db_session.rollback()
            return None

    async def get_token_data(self, token: str) -> Union[RefreshToken, None]:
        query = select(RefreshToken).where(RefreshToken.token == token)
        result = await self.db_session.execute(query)
        token_row = result.fetchone()
        if token_row:
            return token_row[0]
