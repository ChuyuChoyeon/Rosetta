from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CategorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    slug: str


class TagSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    slug: str
    color: str


class AuthorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    username: str
    nickname: Optional[str] = None


class PostSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    slug: str
    content: str
    views: int
    created_at: datetime
    is_pinned: bool = False

    author: AuthorSchema
    category: Optional[CategorySchema] = None


class FriendLinkSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    url: str
    description: Optional[str] = ""
    logo: Optional[object] = None  # ImageField
    is_active: bool
    order: int
