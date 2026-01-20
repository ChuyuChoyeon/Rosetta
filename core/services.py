import random
import string
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from faker import Faker
from blog.models import Category, Comment, Post, Tag
from users.models import UserTitle, Notification
from core.models import FriendLink, Navigation, SearchPlaceholder

class MockDataGenerator:
    """
    Rosetta 博客系统 Mock 数据生成器
    
    用于生成丰富的测试数据，包括用户、文章、评论、标签等。
    """
    def __init__(self, locale="zh_CN"):
        self.fake = Faker(locale)
        self.User = get_user_model()
        
    def _rand_text(self, length: int = 8) -> str:
        """生成随机字符串"""
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
        return suffix

    def _generate_markdown_content(self) -> str:
        """
        生成丰富的 Markdown 格式文章内容
        
        包含：
        1. 介绍段落
        2. 核心概念 (H2)
        3. 引用块
        4. 详细分析 (H2)
        5. 列表项
        6. 代码块 (Python)
        7. 对比表格 (H2)
        8. 进阶用法 (H2)
        9. 嵌套列表
        10. 代码块 (JSON)
        11. 总结 (H2)
        """
        sections = []
        
        # 标题/简介由文章标题和摘要处理，这里从正文开始。
        
        # 1. 介绍段落
        sections.append(self.fake.paragraph(nb_sentences=6))
        sections.append(self.fake.paragraph(nb_sentences=4))
        
        # 2. 核心概念 (H2)
        sections.append(f"## {self.fake.sentence(nb_words=4).rstrip('.')}")
        sections.append(self.fake.paragraph(nb_sentences=8))
        
        # 引用
        sections.append(f"> {self.fake.paragraph(nb_sentences=3)}")
        
        # 3. 详细分析 (H2)
        sections.append(f"## {self.fake.sentence(nb_words=5).rstrip('.')}")
        sections.append(self.fake.paragraph(nb_sentences=6))
        
        # 列表项
        sections.append(f"### {self.fake.sentence(nb_words=3).rstrip('.')}")
        items = "\n".join([f"- **{self.fake.word()}**: {self.fake.sentence()}" for _ in range(6)])
        sections.append(items)
        
        # 代码块 (Python)
        code_snippet_py = "```python\nimport random\n\ndef generate_magic():\n    magic_number = random.randint(1, 100)\n    return f'Magic: {magic_number}'\n\nclass Wizard:\n    def __init__(self, name):\n        self.name = name\n        self.power = 100\n\n    def cast(self):\n        return generate_magic()\n```"
        sections.append(code_snippet_py)
        
        sections.append(self.fake.paragraph(nb_sentences=5))

        # 4. 对比 (H2)
        sections.append(f"## {self.fake.sentence(nb_words=4).rstrip('.')}")
        
        # 表格
        table = "| 特性 | 方案 A | 方案 B | 方案 C |\n| :--- | :---: | :---: | :---: |\n"
        for _ in range(4):
            table += f"| {self.fake.word()} | {random.randint(1, 100)}ms | {random.randint(1, 100)}ms | {random.randint(1, 100)}ms |\n"
        sections.append(table)
        
        sections.append(self.fake.paragraph(nb_sentences=4))

        # 5. 进阶用法 (H2)
        sections.append(f"## {self.fake.sentence(nb_words=5).rstrip('.')}")
        
        # 嵌套列表
        nested_list = (
            f"1. {self.fake.sentence()}\n"
            f"    1. {self.fake.sentence()}\n"
            f"    2. {self.fake.sentence()}\n"
            f"2. {self.fake.sentence()}\n"
            f"3. {self.fake.sentence()}"
        )
        sections.append(nested_list)

        # 代码块 (JavaScript/JSON)
        code_snippet_js = "```json\n{\n  \"status\": \"success\",\n  \"data\": {\n    \"id\": 101,\n    \"title\": \"Hello World\",\n    \"tags\": [\"test\", \"mock\"]\n  }\n}\n```"
        sections.append(code_snippet_js)

        # 6. 总结 (H2)
        sections.append(f"## 总结")
        sections.append(self.fake.paragraph(nb_sentences=5))
        sections.append(f"**{self.fake.sentence()}**")
        
        return "\n\n".join(sections)

    def create_users(self, count=5, password="password123"):
        """生成拥有丰富资料的用户数据"""
        created_users = []
        titles = list(UserTitle.objects.all())
        
        print(f"正在生成 {count} 个用户...")
        for _ in range(count):
            username = self.fake.user_name()
            while self.User.objects.filter(username=username).exists():
                username = f"{username}_{random.randint(100, 999)}"
            
            first_name = self.fake.first_name()
            last_name = self.fake.last_name()
            nickname = f"{last_name}{first_name}" if random.random() > 0.3 else self.fake.user_name()
            
            user = self.User.objects.create_user(
                username=username,
                email=self.fake.email(),
                password=password,
                first_name=first_name,
                last_name=last_name,
                nickname=nickname,
                bio=self.fake.text(max_nb_chars=200),
                website=self.fake.url() if random.random() > 0.5 else "",
                github=f"https://github.com/{username}" if random.random() > 0.5 else "",
                date_joined=self.fake.date_time_this_year(tzinfo=timezone.get_current_timezone()),
            )
            
            if titles and random.random() > 0.7:
                user.title = random.choice(titles)
                user.save()
                
            created_users.append(user)
        return created_users

    def create_categories(self, count=5):
        """生成分类数据"""
        created_categories = []
        existing_names = set(Category.objects.values_list('name', flat=True))
        
        tech_categories = [
            "Python", "Django", "JavaScript", "React", "Vue", 
            "DevOps", "Docker", "Kubernetes", "Linux", 
            "Algorithm", "Data Structure", "Machine Learning", "AI",
            "Web Development", "Database", "PostgreSQL", "Redis",
            "Software Engineering", "System Design", "Career"
        ]
        
        potential_names = [name for name in tech_categories if name not in existing_names]
        while len(potential_names) < count:
            potential_names.append(self.fake.word().capitalize() + " Tech")
            
        print(f"正在生成 {count} 个分类...")
        for name in potential_names[:count]:
            slug = self.fake.unique.slug()
            while Category.objects.filter(slug=slug).exists():
                slug = f"{slug}-{self._rand_text(4)}"
                
            category = Category.objects.create(
                name=name,
                slug=slug,
                description=self.fake.sentence(),
                icon="folder",
                color="primary"
            )
            created_categories.append(category)
        return created_categories

    def create_tags(self, count=10):
        """生成标签数据"""
        created_tags = []
        print(f"正在生成 {count} 个标签...")
        for _ in range(count):
            name = self.fake.word()
            slug = self.fake.unique.slug()
            
            if not Tag.objects.filter(slug=slug).exists():
                tag = Tag.objects.create(
                    name=name,
                    slug=slug,
                    color=random.choice([c[0] for c in Tag.COLOR_CHOICES]),
                    is_active=True
                )
                created_tags.append(tag)
        return created_tags

    def create_posts(self, count=20, users=None, categories=None, tags=None):
        """生成丰富的文章数据"""
        if not users:
            users = list(self.User.objects.all())
        if not categories:
            categories = list(Category.objects.all())
        if not tags:
            tags = list(Tag.objects.all())
            
        created_posts = []
        print(f"正在生成 {count} 篇文章...")
        
        for _ in range(count):
            author = random.choice(users) if users else None
            if not author: break

            category = random.choice(categories) if categories else None
            
            title = self.fake.sentence(nb_words=6, variable_nb_words=True).rstrip(".")
            slug = self.fake.unique.slug()
            while Post.objects.filter(slug=slug).exists():
                slug = f"{slug}-{self._rand_text(4)}"
            
            created_at = self.fake.date_time_this_year(tzinfo=timezone.get_current_timezone())
            
            post = Post.objects.create(
                title=title,
                slug=slug,
                content=self._generate_markdown_content(),
                excerpt=self.fake.text(max_nb_chars=150),
                author=author,
                category=category,
                status="published" if random.random() > 0.1 else "draft",
                views=random.randint(10, 10000),
                created_at=created_at,
                updated_at=created_at,
                is_pinned=random.random() > 0.95,
                allow_comments=True
            )
            
            if tags:
                post.tags.set(random.sample(tags, k=random.randint(1, min(5, len(tags)))))
                
            if users:
                likers = random.sample(users, k=random.randint(0, min(10, len(users))))
                post.likes.set(likers)
                
            created_posts.append(post)
        return created_posts

    def create_comments(self, count=50, users=None, posts=None):
        """生成评论数据 (支持嵌套回复)"""
        if not users:
            users = list(self.User.objects.all())
        if not posts:
            posts = list(Post.objects.all())
            
        created_comments = []
        print(f"正在生成 {count} 条评论...")
        
        for _ in range(count):
            user = random.choice(users)
            post = random.choice(posts)
            
            parent = None
            existing_comments = list(post.comments.all())
            if existing_comments and random.random() > 0.7:
                parent = random.choice(existing_comments)
                if parent.parent:
                    parent = parent.parent
            
            comment = Comment.objects.create(
                post=post,
                user=user,
                parent=parent,
                content=self.fake.paragraph(nb_sentences=random.randint(1, 5)),
                created_at=self.fake.date_time_between(start_date=post.created_at, tzinfo=timezone.get_current_timezone()),
                active=True
            )
            created_comments.append(comment)
            
            if parent and parent.user != user:
                Notification.objects.create(
                    recipient=parent.user,
                    actor=user,
                    verb="回复了你的评论",
                    content_type=ContentType.objects.get_for_model(Comment),
                    object_id=comment.id,
                    timestamp=comment.created_at
                )
            elif post.author != user:
                Notification.objects.create(
                    recipient=post.author,
                    actor=user,
                    verb="评论了你的文章",
                    content_type=ContentType.objects.get_for_model(Comment),
                    object_id=comment.id,
                    timestamp=comment.created_at
                )
        return created_comments

    def create_friend_links(self, count=5):
        """生成友情链接数据"""
        created_links = []
        print(f"正在生成 {count} 个友情链接...")
        
        tech_sites = [
            ("Django Official", "https://www.djangoproject.com/"),
            ("Python", "https://www.python.org/"),
            ("Tailwind CSS", "https://tailwindcss.com/"),
            ("GitHub", "https://github.com/"),
            ("Stack Overflow", "https://stackoverflow.com/"),
            ("Real Python", "https://realpython.com/"),
            ("Hacker News", "https://news.ycombinator.com/"),
        ]
        
        for i in range(count):
            if i < len(tech_sites):
                name, url = tech_sites[i]
            else:
                name = self.fake.company()
                url = self.fake.url()
                
            if not FriendLink.objects.filter(name=name).exists():
                link = FriendLink.objects.create(
                    name=name,
                    url=url,
                    description=self.fake.catch_phrase(),
                    order=i,
                    is_active=True
                )
                created_links.append(link)
        return created_links

    def create_navigations(self):
        """生成默认导航菜单"""
        print("正在生成导航菜单...")
        navs = [
            {"title": "首页", "url": "/", "order": 1, "location": "header"},
            {"title": "文章", "url": "/posts/", "order": 2, "location": "header"},
            {"title": "归档", "url": "/archives/", "order": 3, "location": "header"},
            {"title": "关于", "url": "/about/", "order": 4, "location": "header"},
            {"title": "联系", "url": "/contact/", "order": 5, "location": "header"},
        ]
        created_navs = []
        for item in navs:
            if not Navigation.objects.filter(title=item["title"], location=item["location"]).exists():
                nav = Navigation.objects.create(**item)
                created_navs.append(nav)
        return created_navs

    def create_search_placeholders(self):
        """生成搜索占位符数据"""
        print("正在生成搜索占位符...")
        texts = [
            "搜索 Python...", "搜索 Django...", "搜索 Tailwind...", 
            "如何部署...", "REST API...", "Docker 教程..."
        ]
        created_placeholders = []
        for i, text in enumerate(texts):
            if not SearchPlaceholder.objects.filter(text=text).exists():
                ph = SearchPlaceholder.objects.create(text=text, order=i)
                created_placeholders.append(ph)
        return created_placeholders

def generate_mock_data(
    users_count=5,
    categories_count=5,
    tags_count=10,
    posts_count=20,
    comments_count=60,
    password="password123",
    generate_extras=True,
):
    """
    Mock 数据生成器入口函数
    
    协调 MockDataGenerator 生成各类测试数据。
    使用事务保证数据一致性。
    """
    generator = MockDataGenerator()
    
    with transaction.atomic():
        users = generator.create_users(users_count, password)
        categories = generator.create_categories(categories_count)
        tags = generator.create_tags(tags_count)
        posts = generator.create_posts(posts_count, users, categories, tags)
        comments = generator.create_comments(comments_count, users, posts)
        
        friend_links = []
        navigations = []
        placeholders = []
        
        if generate_extras:
            friend_links = generator.create_friend_links()
            navigations = generator.create_navigations()
            placeholders = generator.create_search_placeholders()
        
    return {
        "users": len(users),
        "categories": len(categories),
        "tags": len(tags),
        "posts": len(posts),
        "comments": len(comments),
        "friend_links": len(friend_links),
        "navigations": len(navigations),
        "placeholders": len(placeholders),
    }
