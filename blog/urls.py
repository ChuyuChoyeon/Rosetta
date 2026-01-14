from django.urls import path
from .views import (
    HomeView,
    PostDetailView,
    CategoryListView,
    TagListView,
    PostByCategoryView,
    PostByTagView,
    SearchView,
    delete_comment,
    subscribe_view,
    unsubscribe_view,
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("post/<slug:slug>/", PostDetailView.as_view(), name="post_detail"),
    path("categories/", CategoryListView.as_view(), name="category_list"),
    path("category/<slug:slug>/", PostByCategoryView.as_view(), name="post_by_category"),
    path("tags/", TagListView.as_view(), name="tag_list"),
    path("tag/<slug:slug>/", PostByTagView.as_view(), name="post_by_tag"),
    path("search/", SearchView.as_view(), name="search"),
    path("articles/", HomeView.as_view(), name="post_list"),  # Alias for now
    path("comment/<int:pk>/delete/", delete_comment, name="delete_comment"),
    path("subscribe/", subscribe_view, name="subscribe"),
    path("unsubscribe/<uuid:token>/", unsubscribe_view, name="unsubscribe"),
]
