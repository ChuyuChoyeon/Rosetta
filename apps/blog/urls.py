from django.urls import path
from .views import (
    HomeView,
    PostDetailView,
    CategoryListView,
    TagListView,
    PostByCategoryView,
    PostByTagView,
    SearchView,
    ArchiveView,
    delete_comment,
)
from .feeds import LatestPostsFeed

urlpatterns = [
    # 首页 (Home Page)
    # 展示置顶文章和最新文章列表
    path("", HomeView.as_view(), name="home"),
    
    # RSS Feed (订阅源)
    # 提供网站文章的 RSS 2.0 订阅
    path("feed/", LatestPostsFeed(), name="post_feed"),
    
    # 文章详情 (Post Detail)
    # 通过 Slug 访问文章
    path("post/<slug:slug>/", PostDetailView.as_view(), name="post_detail"),
    
    # 分类列表与详情 (Categories)
    path("categories/", CategoryListView.as_view(), name="category_list"),
    path(
        "category/<slug:slug>/", PostByCategoryView.as_view(), name="post_by_category"
    ),
    
    # 标签列表与详情 (Tags)
    path("tags/", TagListView.as_view(), name="tag_list"),
    path("tag/<slug:slug>/", PostByTagView.as_view(), name="post_by_tag"),
    
    # 搜索 (Search)
    # 全文搜索页面
    path("search/", SearchView.as_view(), name="search"),
    
    # 归档 (Archives)
    # 按时间归档的文章列表
    path("archives/", ArchiveView.as_view(), name="archive"),
    
    # 全部文章 (All Posts)
    # 分页展示所有已发布文章
    path(
        "posts/",
        HomeView.as_view(template_name="blog/all_posts.html", paginate_by=12),
        name="post_list",
    ),
    
    # 文章列表别名 (Keep for backward compatibility)
    path("articles/", HomeView.as_view(), name="article_list_alias"),
    
    # 评论删除 (Comment Deletion)
    # AJAX 接口
    path("comment/<int:pk>/delete/", delete_comment, name="delete_comment"),
]
