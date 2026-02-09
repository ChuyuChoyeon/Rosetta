from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Comment, Post, Category, Tag
from users.models import Notification, User
from .schemas import CommentCreateSchema, PostCreateSchema
from constance import config
import re
from typing import Optional


def create_comment(post: Post, user: User, data: CommentCreateSchema) -> Comment:
    """
    创建评论并处理相关通知 (使用 Pydantic Schema)

    Args:
        post: 评论所属的文章对象
        user: 评论发布者
        data: 包含评论内容和父评论 ID 的 Pydantic Schema

    Returns:
        Comment: 创建的评论对象
    """
    with transaction.atomic():
        # Determine if comment should be active immediately
        require_approval = getattr(config, "COMMENT_REQUIRE_APPROVAL", False)
        is_active = True
        if require_approval:
            # Staff and superusers bypass approval
            if not (user.is_staff or user.is_superuser):
                is_active = False

        comment = Comment(post=post, user=user, content=data.content, active=is_active)

        parent_comment = None
        # 处理父评论（回复）
        if data.parent_id:
            try:
                parent_comment = Comment.objects.get(id=data.parent_id, post=post)
                comment.parent = parent_comment
            except Comment.DoesNotExist:
                pass

        comment.save()

        # 通知被回复的用户
        if parent_comment and parent_comment.user != user:
            Notification.objects.create(
                recipient=parent_comment.user,
                actor=user,
                verb="回复了你的评论",
                target=comment,
            )

        # 处理 @提及
        mentions = re.findall(r"@(\w+)", data.content)
        for username in set(mentions):  # 去重
            try:
                target_user = User.objects.get(username=username)
                if target_user != user:  # 不通知自己
                    Notification.objects.create(
                        recipient=target_user,
                        actor=user,
                        verb="在评论中提到了你",
                        target=comment,
                    )
            except User.DoesNotExist:
                pass

        return comment


def create_post_service(user: User, data: PostCreateSchema) -> Post:
    """
    创建文章服务

    Args:
        user: 文章作者
        data: 包含文章信息的 Pydantic Schema

    Returns:
        Post: 创建的文章对象
    """
    with transaction.atomic():
        category = None
        if data.category_id:
            try:
                category = Category.objects.get(id=data.category_id)
            except Category.DoesNotExist:
                raise ValidationError(
                    f"Category with id {data.category_id} does not exist"
                )

        post = Post.objects.create(
            author=user,
            title=data.title,
            content=data.content,
            status=data.status,
            category=category,
        )

        # 处理标签
        if data.tags:
            for tag_name in data.tags:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                post.tags.add(tag)

        return post
