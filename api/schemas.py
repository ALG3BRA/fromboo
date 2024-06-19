from datetime import datetime
from typing import Optional, Union
import uuid
from fastapi import HTTPException
from pydantic import BaseModel
from pydantic import EmailStr


class TunedModel(BaseModel):
    class Config:
        """tells pydantic to convert even non dict obj to json"""

        orm_mode = True


class UserCreate(TunedModel):
    name: str
    email: EmailStr
    password: str


class ShowUser(TunedModel):
    user_id: uuid.UUID
    name: str
    email: EmailStr
    is_active: bool


class ShowWordFromBase(TunedModel):
    word_id: uuid.UUID
    word: str


class ShowUserWords(TunedModel):
    bundle_id: uuid.UUID
    user_id: uuid.UUID
    word_id: uuid.UUID
    translation_id: uuid.UUID
    time: datetime
    is_favorite: bool


class ShowTranslation(TunedModel):
    translation_id: uuid.UUID
    word_id: uuid.UUID
    translation: str
    pos: str


class Token(TunedModel):
    access_token: str
    exp: datetime
    token_type: str


class CustomTranslation(TunedModel):
    word_id: uuid.UUID
    translation: str
    pos: str