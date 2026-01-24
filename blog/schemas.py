from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


class CommentCreateSchema(BaseModel):
    """
    Schema for creating a comment.

    Attributes:
        content (str): The content of the comment. Must be between 1 and 1000 characters.
        parent_id (Optional[int]): The ID of the parent comment if this is a reply. Defaults to None.
    """

    content: str = Field(
        ..., min_length=1, max_length=1000, description="The content of the comment"
    )
    parent_id: Optional[int] = Field(
        None, description="The ID of the parent comment if this is a reply"
    )


class PostCreateSchema(BaseModel):
    """
    Schema for creating a blog post.

    Attributes:
        title (str): The title of the post. Must be between 1 and 200 characters.
        content (str): The content of the post.
        status (str): The status of the post. Either 'draft' or 'published'. Defaults to 'draft'.
        category_id (Optional[int]): The ID of the category. Defaults to None.
        tags (List[str]): List of tag names. Defaults to empty list.
    """

    title: str = Field(
        ..., min_length=1, max_length=200, description="The title of the post"
    )
    content: str = Field(..., min_length=1, description="The content of the post")
    status: str = Field(
        default="draft",
        pattern="^(draft|published)$",
        description="The status of the post",
    )
    category_id: Optional[int] = Field(None, description="The ID of the category")
    tags: List[str] = Field(default_factory=list, description="List of tag names")

    @field_validator("title")
    def title_must_not_be_empty(cls, v):
        """Validates that the title is not empty or whitespace only."""
        if not v.strip():
            raise ValueError("Title must not be empty")
        return v
