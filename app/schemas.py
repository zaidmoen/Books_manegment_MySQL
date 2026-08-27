from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class BookFields(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=120)
    published_year: int = Field(gt=0)

    @field_validator("title", "author")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("published_year")
    @classmethod
    def validate_year(cls, value: int) -> int:
        if value > datetime.now().year:
            raise ValueError("published_year cannot be in the future")
        return value


class BookCreate(BookFields):
    pass


class BookUpdate(BookFields):
    pass


class BookPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    author: str | None = Field(default=None, min_length=1, max_length=120)
    published_year: int | None = Field(default=None, gt=0)

    @field_validator("title", "author")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("published_year")
    @classmethod
    def validate_optional_year(cls, value: int | None) -> int | None:
        if value is not None and value > datetime.now().year:
            raise ValueError("published_year cannot be in the future")
        return value


class BookResponse(BookFields):
    id: int


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    role: Literal["user", "admin"] = "user"

    @field_validator("username")
    @classmethod
    def clean_username(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("username must not be empty")
        return value


class UserResponse(BaseModel):
    id: int
    username: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str
