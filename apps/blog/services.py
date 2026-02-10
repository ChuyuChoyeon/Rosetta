from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Comment, Post, Category, Tag
from users.models import Notification, User
from .schemas import CommentCreateSchema, PostCreateSchema
from constance import config
import re


def create_comment(post: Post, user: User, data: CommentCreateSchema) -> Comment:
    """
    创建评论并处理相关通知。

    使用 Pydantic Schema 进行数据验证。如果配置了评论审核，非管理员用户的评论默认为非激活状态。

    Args:
        post: 评论所属的文章对象。
        user: 评论的发布者用户对象。
        data: 包含评论内容和父评论 ID 的数据对象 (Pydantic Schema)。

    Returns:
        Comment: 创建并保存的评论模型实例。
    """
    with transaction.atomic():
        # 检查是否需要审核
        require_approval = getattr(config, "COMMENT_REQUIRE_APPROVAL", False)
        is_active = True
        if require_approval:
            # 管理员和超级用户免审核
            if not (user.is_staff or user.is_superuser):
                is_active = False

        comment = Comment(post=post, user=user, content=data.content, active=is_active)

        parent_comment = None
        # 处理父评论（回复逻辑）
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
    创建文章的核心服务逻辑。

    负责创建文章对象、处理分类关联以及标签的自动创建和绑定。

    Args:
        user: 文章的作者用户对象。
        data: 包含文章标题、内容、状态、分类和标签的数据对象 (Pydantic Schema)。

    Returns:
        Post: 创建并保存的文章模型实例。

    Raises:
        ValidationError: 当指定的分类 ID 不存在时抛出。
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
