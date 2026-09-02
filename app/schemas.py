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


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=1, max_length=2000)

    @field_validator("comment")
    @classmethod
    def strip_comment(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("comment must not be empty")
        return value


class ReviewResponse(ReviewCreate):
    id: int
    user_id: int
    book_id: int
    created_at: datetime


class SchoolFields(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    address: str | None = Field(default=None, max_length=255)
    principal_name: str | None = Field(default=None, max_length=120)

    @field_validator("name", "address", "principal_name")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class SchoolCreate(SchoolFields):
    pass


class SchoolUpdate(SchoolFields):
    pass


class SchoolPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    address: str | None = Field(default=None, max_length=255)
    principal_name: str | None = Field(default=None, max_length=120)

    @field_validator("name", "address", "principal_name")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class SchoolResponse(SchoolFields):
    id: int


class SchoolClassFields(BaseModel):
    school_id: int = Field(gt=0)
    grade_level: str = Field(min_length=1, max_length=50)
    section: str = Field(min_length=1, max_length=20)
    room_number: str | None = Field(default=None, max_length=20)
    capacity: int = Field(gt=0, le=200)

    @field_validator("grade_level", "section", "room_number")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class SchoolClassCreate(SchoolClassFields):
    pass


class SchoolClassUpdate(SchoolClassFields):
    pass


class SchoolClassPatch(BaseModel):
    school_id: int | None = Field(default=None, gt=0)
    grade_level: str | None = Field(default=None, min_length=1, max_length=50)
    section: str | None = Field(default=None, min_length=1, max_length=20)
    room_number: str | None = Field(default=None, max_length=20)
    capacity: int | None = Field(default=None, gt=0, le=200)

    @field_validator("grade_level", "section", "room_number")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class SchoolClassResponse(SchoolClassFields):
    id: int
    school_name: str


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
