import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy import Boolean, TIMESTAMP
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean(), default=True)
    hashed_password = Column(String, nullable=False)


class RefreshToken(Base):
    __tablename__ = "refresh_token"

    token = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), unique=True)
    registered_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)
    ip_address = Column(String, nullable=False)


class WordBase(Base):
    __tablename__ = "word_base"

    word_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    word = Column(String, nullable=False, unique=True)


class Translation(Base):
    __tablename__ = "translation"

    translation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    word_id = Column(UUID(as_uuid=True), ForeignKey('word_base.word_id'), nullable=False)
    translation = Column(String, nullable=False)
    pos = Column(String)

    __table_args__ = (
        UniqueConstraint('word_id', 'translation', name='uq_word_id_and_translation'),
    )


class UserWords(Base):
    __tablename__ = "user_words"

    bundle_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    word_id = Column(UUID(as_uuid=True), ForeignKey('word_base.word_id'), nullable=False)
    translation_id = Column(UUID(as_uuid=True), ForeignKey('translation.translation_id'), nullable=False)
    added_at = Column(TIMESTAMP, default=datetime.utcnow)
    is_favorite = Column(Boolean(), default=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'word_id', 'translation_id', name='uq_user_and_word_and_translation_id'),
    )
