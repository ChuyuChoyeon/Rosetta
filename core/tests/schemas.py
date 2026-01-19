from pydantic import BaseModel, HttpUrl, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

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
    # ImageField returns a complex object, so we might mock or just check string if using .url
    # For simplicity in context validation, we check attributes present on the model instance
    views: int
    created_at: datetime
    is_pinned: bool = False
    
    # Relationships
    author: AuthorSchema
    category: Optional[CategorySchema] = None
    # ManyToMany is harder to validate directly from model instance without prefetching
    # tags: List[TagSchema] 

class FriendLinkSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    url: str
    description: Optional[str] = ""
    logo: Optional[object] = None # ImageField
    is_active: bool
    order: int
