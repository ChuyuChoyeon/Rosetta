from django.core.management.base import BaseCommand
from core.services import generate_mock_data


class Command(BaseCommand):
    help = "生成 mock 数据（用户、分类、文章、评论）"

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=5)
        parser.add_argument("--categories", type=int, default=5)
        parser.add_argument("--posts", type=int, default=20)
        parser.add_argument("--comments", type=int, default=60)
        parser.add_argument("--password", type=str, default="password123")

    def handle(self, *args, **options):
        users_count = max(0, int(options["users"]))
        categories_count = max(0, int(options["categories"]))
        posts_count = max(0, int(options["posts"]))
        comments_count = max(0, int(options["comments"]))
        password = str(options["password"])

        generate_mock_data(
            users_count=users_count,
            categories_count=categories_count,
            posts_count=posts_count,
            comments_count=comments_count,
            password=password,
        )

        self.stdout.write(self.style.SUCCESS("mock 数据已生成"))
