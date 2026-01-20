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
    subscribe_view,
    unsubscribe_view,
)

urlpatterns = [
    # 首页
    path("", HomeView.as_view(), name="home"),
    
    # 文章详情
    path("post/<slug:slug>/", PostDetailView.as_view(), name="post_detail"),
    
    # 分类列表与详情
    path("categories/", CategoryListView.as_view(), name="category_list"),
    path("category/<slug:slug>/", PostByCategoryView.as_view(), name="post_by_category"),
    
    # 标签列表与详情
    path("tags/", TagListView.as_view(), name="tag_list"),
    path("tag/<slug:slug>/", PostByTagView.as_view(), name="post_by_tag"),
    
    # 搜索
    path("search/", SearchView.as_view(), name="search"),
    
    # 归档
    path("archives/", ArchiveView.as_view(), name="archive"),

    # 全部文章
    path("posts/", HomeView.as_view(template_name="blog/all_posts.html", paginate_by=12), name="post_list"),

    # 文章列表别名 (Keep for backward compatibility)
    path("articles/", HomeView.as_view(), name="article_list_alias"),
    
    # 评论删除
    path("comment/<int:pk>/delete/", delete_comment, name="delete_comment"),
    
    # 订阅与退订
    path("subscribe/", subscribe_view, name="subscribe"),
    path("unsubscribe/<uuid:token>/", unsubscribe_view, name="unsubscribe"),
]
