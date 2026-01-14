import random
import string
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from faker import Faker
from blog.models import Category, Comment, Post


def _rand_text(prefix: str, length: int = 8) -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{prefix}-{suffix}"


def generate_mock_data(
    users_count=5,
    categories_count=5,
    posts_count=20,
    comments_count=60,
    password="password123",
):
    """
    Generates mock data for the application using Faker and random data.
    Returns a dictionary with counts of created objects.
    """
    User = get_user_model()
    fake = Faker("zh_CN")
    created = {"users": 0, "categories": 0, "posts": 0, "comments": 0}

    with transaction.atomic():
        # Users
        users = []
        for _ in range(users_count):
            username = fake.user_name()
            # Ensure unique username
            while User.objects.filter(username=username).exists():
                username = f"{username}_{random.randint(100, 999)}"

            user = User.objects.create_user(
                username=username,
                email=fake.email(),
                password=password,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                bio=fake.text(max_nb_chars=200),
                date_joined=fake.date_time_this_year(
                    tzinfo=timezone.get_current_timezone()
                ),
            )
            users.append(user)
        created["users"] = len(users)

        # Categories
        categories = []
        for _ in range(categories_count):
            name = fake.word() + "分类"
            if not Category.objects.filter(name=name).exists():
                categories.append(
                    Category.objects.create(
                        name=name, slug=fake.unique.slug(), description=fake.sentence()
                    )
                )
        created["categories"] = len(categories)

        # Posts
        posts = []
        target_users = users if users else list(User.objects.all())
        target_categories = categories if categories else list(Category.objects.all())

        if target_users:
            for _ in range(posts_count):
                author = random.choice(target_users)
                category = (
                    random.choice(target_categories) if target_categories else None
                )

                posts.append(
                    Post.objects.create(
                        title=fake.sentence(nb_words=6, variable_nb_words=True)[:-1],
                        slug=fake.unique.slug(),
                        content=f"<p>{'</p><p>'.join(fake.paragraphs(nb=3))}</p>",
                        excerpt=fake.text(max_nb_chars=150),
                        author=author,
                        category=category,
                        status="published",
                        views=random.randint(0, 5000),
                        created_at=fake.date_time_this_year(
                            tzinfo=timezone.get_current_timezone()
                        ),
                    )
                )
            created["posts"] = len(posts)

        # Comments
        all_users = list(User.objects.all())
        all_posts = list(Post.objects.all())

        if all_users and all_posts:
            for _ in range(comments_count):
                Comment.objects.create(
                    post=random.choice(all_posts),
                    user=random.choice(all_users),
                    content=fake.sentence(nb_words=10),
                    active=True,
                    created_at=fake.date_time_this_year(
                        tzinfo=timezone.get_current_timezone()
                    ),
                )
            created["comments"] = comments_count

    return created
