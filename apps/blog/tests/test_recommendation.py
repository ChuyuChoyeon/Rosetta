import pytest
from django.urls import reverse
from django.utils import timezone
from blog.models import Post, Category, Tag, PostViewHistory, Comment
from users.models import User
from datetime import timedelta

@pytest.mark.django_db
class TestRecommendationSystem:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        self.user = User.objects.create_user(username="reader", password="password")
        self.author = User.objects.create_user(username="author", password="password")
        
        # Categories
        self.cat_python = Category.objects.create(name="Python", slug="python")
        self.cat_rust = Category.objects.create(name="Rust", slug="rust")
        
        # Tags
        self.tag_django = Tag.objects.create(name="Django", slug="django")
        self.tag_async = Tag.objects.create(name="Async", slug="async")
        self.tag_web = Tag.objects.create(name="Web", slug="web")
        
        # Posts
        now = timezone.now()
        
        # 1. Relevant Post (Matches User Interest)
        self.post_python_django = Post.objects.create(
            title="Python Django Guide",
            slug="python-django-guide",
            content="Content",
            author=self.author,
            category=self.cat_python,
            status="published",
            published_at=now,
            views=100
        )
        self.post_python_django.tags.add(self.tag_django, self.tag_web)
        
        # 2. Popular Post (High Engagement but maybe less relevant)
        self.post_popular = Post.objects.create(
            title="Viral Rust Post",
            slug="viral-rust-post",
            content="Content",
            author=self.author,
            category=self.cat_rust,
            status="published",
            published_at=now,
            views=10000 
        )
        self.post_popular.tags.add(self.tag_async)
        # Add likes/comments manually if needed, or rely on views for now
        # (The algo uses likes/comments count, need to create them for full effect)
        
        # 3. Old Post
        self.post_old = Post.objects.create(
            title="Old Python Post",
            slug="old-python-post",
            content="Content",
            author=self.author,
            category=self.cat_python,
            status="published",
            published_at=now - timedelta(days=60),
            views=50
        )
        
        # 4. Irrelevant Post
        self.post_irrelevant = Post.objects.create(
            title="Random Post",
            slug="random-post",
            content="Content",
            author=self.author,
            category=self.cat_rust,
            status="published",
            published_at=now,
            views=10
        )

        self.url = reverse("home")

    def test_cold_start_recommendation(self):
        """Test recommendation for anonymous or new user (Cold Start)"""
        # Anonymous
        response = self.client.get(self.url, {"filter": "recommended"})
        assert response.status_code == 200
        # Should fallback to latest/pinned logic for anonymous usually, 
        # BUT the view logic says: if user.is_authenticated: ... else: order_by("-is_pinned", "-views", ...)
        # So for anonymous, it sorts by views (secondary).
        
        posts = list(response.context["posts"])
        # post_popular has 10000 views, post_python_django has 100
        assert posts[0] == self.post_popular
        assert posts[1] == self.post_python_django

    def test_authenticated_user_recommendation(self):
        """Test recommendation for authenticated user with history"""
        self.client.force_login(self.user)
        
        # Simulate User History: User read a Python/Django post
        # Create history entry
        PostViewHistory.objects.create(
            user=self.user,
            post=self.post_python_django,
            viewed_at=timezone.now()
        )
        
        # Now request recommendations
        response = self.client.get(self.url, {"filter": "recommended"})
        assert response.status_code == 200
        
        posts = list(response.context["posts"])
        
        # Algorithm weights:
        # Relevance: Tag Match (50) + Category Match (100)
        # Engagement: Ln(Views+1)*4 + Likes*5 + Comments*10
        # Recency: <7 days (+50), <30 days (+20)
        
        # post_python_django:
        #   Relevance: 100 (Category match) + 100 (2 tags match? No, we viewed this post, so its tags are "viewed_tags")
        #   Actually, the algo extracts tags from viewed posts. 
        #   So user prefers "Python" (cat) and "Django", "Web" (tags).
        #   post_python_django matches ALL of these.
        #   Relevance = 50*2 (tags) + 100 (cat) = 200.
        #   Engagement = Ln(101)*4 ≈ 4.6*4 ≈ 18.
        #   Recency = 50.
        #   Total ≈ 268.
        
        # post_popular (Rust, Async):
        #   Relevance: 0.
        #   Engagement = Ln(10001)*4 ≈ 9.2*4 ≈ 37.
        #   Recency = 50.
        #   Total ≈ 87.
        
        # So post_python_django should be first.
        # post_old (Old Python Post) has Relevance (100 for Category) + Engagement (~15) + Recency (0) = ~115.
        # post_popular (Viral Rust Post) has Relevance (0) + Engagement (~37) + Recency (50) = ~87.
        
        # So order should be: post_python_django, post_old, post_popular
        
        assert posts[0] == self.post_python_django
        assert posts[1] == self.post_old
        assert posts[2] == self.post_popular

    def test_recommendation_engagement_impact(self):
        """Test that high engagement can boost a post"""
        self.client.force_login(self.user)
        
        # No history, so it falls back to "Cold Start" logic inside the authenticated block?
        # The code says: if viewed_tag_ids or viewed_category_ids: ... else: # Cold start
        
        # Let's add LOTS of likes/comments to post_popular
        for _ in range(10):
            u = User.objects.create_user(username=f"fan_{_}", password="p")
            self.post_popular.likes.add(u)
            Comment.objects.create(post=self.post_popular, user=u, content="Wow", active=True)
            
        # Engagement Score boost:
        # Likes: 10 * 5 = 50
        # Comments: 10 * 10 = 100
        # Total boost = 150.
        
        response = self.client.get(self.url, {"filter": "recommended"})
        posts = list(response.context["posts"])
        
        # Since we have NO history, it uses the "else" block (Cold Start for Auth User).
        # Logic: Engagement + Recency.
        # post_popular should be top because of views + likes + comments.
        assert posts[0] == self.post_popular

    def test_archive_view(self):
        """Test Archive View context and SEO"""
        url = reverse("archive")
        response = self.client.get(url)
        assert response.status_code == 200
        assert "meta" in response.context
        assert "posts" in response.context
        assert len(response.context["posts"]) >= 4
