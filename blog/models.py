from django.contrib.auth.models import User
from django.db import models
from taggit.managers  import TaggableManager
# Create your models here.

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey("Category", on_delete=models.CASCADE)
    tags = TaggableManager()
    status = models.CharField(max_length=10, choices=[('draft', 'Draft'), ('published', 'Published')], default='draft')
    slug = models.SlugField(max_length=200, unique=True)
    image = models.ImageField(upload_to='blog/images/', blank=True, null=True)
    views = models.PositiveIntegerField(default=0)
    published_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    meta_keywords = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=[('approved', 'Approved'), ('pending', 'Pending')], default='pending')

    def __str__(self):
        return f'Comment by {self.author} on {self.post}'

class Link(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
