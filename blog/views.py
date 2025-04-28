from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.syndication.views import Feed
from django.http import Http404
from django.utils.feedgenerator import Atom1Feed
from django.db.models import Q
from django.db.models import Count
from django.db.models.functions import TruncYear, TruncMonth
from wagtail.models import Page
from .models import BlogPage, BlogCategory, BlogPageTag
from django.shortcuts import render, get_object_or_404
from django.utils.text import slugify

class BlogIndexView(ListView):
    model = BlogPage
    template_name = 'blog/blog_index.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        return BlogPage.objects.live().order_by('-first_published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = BlogCategory.objects.all()
        
        # 为列表中的每篇文章添加 author_name 属性
        for post in context['posts']:
            if post.author:
                # 确保作者的 get_full_name 方法返回内容，如果为空则使用用户名
                author_name = post.author.get_full_name() or post.author.username
                post.author_name = author_name
            else:
                post.author_name = "未知作者"
                
        return context

class BlogCategoryView(ListView):
    template_name = 'blog/blog_category.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(BlogCategory, slug=self.kwargs['slug'])
        return BlogPage.objects.live().filter(categories=self.category).order_by('-first_published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['categories'] = BlogCategory.objects.all()  # 添加分类列表到上下文
        
        # 为列表中的每篇文章添加 author_name 属性
        for post in context['posts']:
            if post.author:
                # 确保作者的 get_full_name 方法返回内容，如果为空则使用用户名
                author_name = post.author.get_full_name() or post.author.username
                post.author_name = author_name
            else:
                post.author_name = "未知作者"
                
        return context

class BlogTagView(ListView):
    template_name = 'blog/blog_tag.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        return BlogPage.objects.live().filter(tags__slug=self.kwargs['tag']).order_by('-first_published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.kwargs['tag']
        context['categories'] = BlogCategory.objects.all()  # 添加分类列表到上下文
        
        # 为列表中的每篇文章添加 author_name 属性
        for post in context['posts']:
            if post.author:
                # 确保作者的 get_full_name 方法返回内容，如果为空则使用用户名
                author_name = post.author.get_full_name() or post.author.username
                post.author_name = author_name
            else:
                post.author_name = "未知作者"
                
        return context

class BlogSearchView(ListView):
    template_name = 'blog/blog_search.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return BlogPage.objects.live().filter(
                Q(title__icontains=query) |
                Q(intro__icontains=query) |
                Q(body__icontains=query)
            ).distinct().order_by('-first_published_at')
        return BlogPage.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['categories'] = BlogCategory.objects.all()  # 添加分类列表到上下文
        context['search_results'] = context['posts']  # 为模板提供搜索结果
        
        # 为列表中的每篇文章添加 author_name 属性
        for post in context['posts']:
            if post.author:
                # 确保作者的 get_full_name 方法返回内容，如果为空则使用用户名
                author_name = post.author.get_full_name() or post.author.username
                post.author_name = author_name
            else:
                post.author_name = "未知作者"
                
        return context

class BlogRSSFeed(Feed):
    title = '我的博客 - RSS Feed'
    link = '/blog/'
    description = '最新博客文章'

    def items(self):
        return BlogPage.objects.live().order_by('-first_published_at')[:10]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.intro

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return item.first_published_at

class BlogAtomFeed(BlogRSSFeed):
    feed_type = Atom1Feed
    subtitle = BlogRSSFeed.description


def blog_detail(request, slug):
    # 尝试直接查找，如果找不到，可能是因为 slug 中包含非 ASCII 字符
    try:
        post = get_object_or_404(BlogPage, slug=slug)
    except:
        # 尝试通过标题查找（对于中文 slug 的情况）
        posts = BlogPage.objects.filter(title__icontains=slug)
        if posts.exists():
            post = posts.first()
        else:
            raise Http404("找不到对应的博客文章")
    
    # 确保作者信息存在，如果不存在设置为None
    if post.author:
        # 确保作者的 get_full_name 方法返回内容，如果为空则使用用户名
        author_name = post.author.get_full_name() or post.author.username
        post.author_name = author_name
    else:
        post.author_name = "未知作者"
    
    categories = BlogCategory.objects.all()
    return render(request, 'blog/blog_detail.html', {
        'post': post,
        'categories': categories
    })

class BlogArchiveIndexView(ListView):
    """博客归档索引视图，显示按年月归档的文章列表"""
    template_name = 'blog/blog_archive.html'
    context_object_name = 'archives'
    
    def get_queryset(self):
        # 按年月对文章进行分组，并计算每个月的文章数量
        archives = BlogPage.objects.live().annotate(
            year=TruncYear('date'),
            month=TruncMonth('date')
        ).values('year', 'month').annotate(
            count=Count('id')
        ).order_by('-year', '-month')
        
        # 格式化结果为更易于模板使用的结构
        result = {}
        for item in archives:
            year = item['year'].year
            month = item['month'].month
            count = item['count']
            
            if year not in result:
                result[year] = []
            
            result[year].append({
                'month': month,
                'count': count,
                'date_str': f"{year}年{month}月"
            })
            
        return result
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = BlogCategory.objects.all()
        return context

class BlogMonthArchiveView(ListView):
    """博客月度归档视图，显示特定年月的所有文章"""
    template_name = 'blog/blog_month_archive.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        year = self.kwargs['year']
        month = self.kwargs['month']
        
        return BlogPage.objects.live().filter(
            date__year=year,
            date__month=month
        ).order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs['year']
        month = self.kwargs['month']
        
        context['year'] = year
        context['month'] = month
        context['date_str'] = f"{year}年{month}月"
        context['categories'] = BlogCategory.objects.all()
        
        # 为列表中的每篇文章添加 author_name 属性
        for post in context['posts']:
            if post.author:
                # 确保作者的 get_full_name 方法返回内容，如果为空则使用用户名
                author_name = post.author.get_full_name() or post.author.username
                post.author_name = author_name
            else:
                post.author_name = "未知作者"
        
        return context