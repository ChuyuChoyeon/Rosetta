from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.forms import CheckboxSelectMultiple
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.search import index
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase
from django.shortcuts import reverse
from django.http import Http404
import uuid

class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'BlogPage',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )

class BlogCategory(models.Model):
    name = models.CharField(max_length=255, verbose_name='分类名称')
    slug = models.SlugField(unique=True, max_length=255, verbose_name='URL别名')
    description = models.TextField(blank=True, verbose_name='分类描述')
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE, verbose_name='父分类')
    
    panels = [
        FieldPanel('name'),
        FieldPanel('slug'),
        FieldPanel('description'),
        FieldPanel('parent'),
    ]
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '博客分类'
        verbose_name_plural = '博客分类'
        ordering = ['name']

class BlogIndexPage(Page):
    intro = RichTextField(blank=True, verbose_name='页面介绍')
    
    content_panels = Page.content_panels + [
        FieldPanel('intro')
    ]
    
    def get_context(self, request):
        context = super().get_context(request)
        blogpages = BlogPage.objects.live().order_by('-first_published_at')
        context['blogpages'] = blogpages
        return context

class BlogPage(Page):
    date = models.DateField(verbose_name='发布日期', default=timezone.now)
    intro = models.CharField(max_length=250, verbose_name='文章简介')
    body = RichTextField(verbose_name='文章内容')
    categories = ParentalManyToManyField('BlogCategory', blank=True, verbose_name='分类')
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True, verbose_name='标签')
    author = models.ForeignKey(
        'auth.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='作者'
    )
    featured_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name='特色图片'
    )
    
    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]
    
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('date'),
            FieldPanel('author'),
        ], heading='文章信息'),
        FieldPanel('featured_image'),
        FieldPanel('intro'),
        FieldPanel('body'),
        MultiFieldPanel([
            FieldPanel('categories', widget=CheckboxSelectMultiple),
            FieldPanel('tags'),
        ], heading='分类和标签'),
    ]
    
    class Meta:
        verbose_name = '博客文章'
        verbose_name_plural = '博客文章'
        
    def save(self, *args, **kwargs):
        # 如果 slug 为空或包含非 ASCII 字符，则生成一个基于标题的英文 slug
        if not self.slug or not self.slug.isascii():
            # 尝试从标题生成 slug
            self.slug = slugify(self.title)
            # 如果 slug 仍然为空（如纯中文标题），则使用 uuid
            if not self.slug:
                self.slug = slugify(str(uuid.uuid4())[:8])
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """返回博客文章的绝对URL"""
        return reverse('blog:blog_detail', kwargs={'slug': self.slug})
