from django.core.management.base import BaseCommand
from core.services import generate_mock_data


class Command(BaseCommand):
    """
    生成测试数据 (Mock Data) 的管理命令
    
    功能：
    调用 core.services.generate_mock_data 生成指定数量的用户、分类、文章和评论。
    
    用法：
    python manage.py generate_mock_data --users 10 --posts 50
    """
    help = "生成 mock 数据（用户、分类、文章、评论）"

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=5, help="生成用户数量 (默认: 5)")
        parser.add_argument("--categories", type=int, default=5, help="生成分类数量 (默认: 5)")
        parser.add_argument("--tags", type=int, default=10, help="生成标签数量 (默认: 10)")
        parser.add_argument("--posts", type=int, default=20, help="生成文章数量 (默认: 20)")
        parser.add_argument("--comments", type=int, default=60, help="生成评论数量 (默认: 60)")
        parser.add_argument("--password", type=str, default="password123", help="默认用户密码")
        parser.add_argument("--no-extras", action="store_true", help="不生成附加数据（友链、导航等）")

    def handle(self, *args, **options):
        users_count = max(0, int(options["users"]))
        categories_count = max(0, int(options["categories"]))
        tags_count = max(0, int(options["tags"]))
        posts_count = max(0, int(options["posts"]))
        comments_count = max(0, int(options["comments"]))
        password = str(options["password"])
        generate_extras = not options["no_extras"]

        self.stdout.write("正在生成测试数据...")
        
        results = generate_mock_data(
            users_count=users_count,
            categories_count=categories_count,
            tags_count=tags_count,
            posts_count=posts_count,
            comments_count=comments_count,
            password=password,
            generate_extras=generate_extras,
        )

        self.stdout.write(self.style.SUCCESS(
            f"成功生成: 用户={results['users']}, 分类={results['categories']}, 标签={results['tags']}, 文章={results['posts']}, 评论={results['comments']}, 友链={results['friend_links']}, 导航={results['navigations']}, 占位符={results['placeholders']}"
        ))
