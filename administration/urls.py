from django.urls import path
from . import views

app_name = "administration"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    # Posts
    path("posts/", views.PostListView.as_view(), name="post_list"),
    path("posts/create/", views.PostCreateView.as_view(), name="post_create"),
    path("posts/<int:pk>/edit/", views.PostUpdateView.as_view(), name="post_edit"),
    path("posts/<int:pk>/delete/", views.PostDeleteView.as_view(), name="post_delete"),
    # Categories
    path("categories/", views.CategoryListView.as_view(), name="category_list"),
    path(
        "categories/create/", views.CategoryCreateView.as_view(), name="category_create"
    ),
    path(
        "categories/<int:pk>/edit/",
        views.CategoryUpdateView.as_view(),
        name="category_edit",
    ),
    path(
        "categories/<int:pk>/delete/",
        views.CategoryDeleteView.as_view(),
        name="category_delete",
    ),
    # Tags
    path("tags/", views.TagListView.as_view(), name="tag_list"),
    path("tags/create/", views.TagCreateView.as_view(), name="tag_create"),
    path("tags/<int:pk>/edit/", views.TagUpdateView.as_view(), name="tag_edit"),
    path("tags/<int:pk>/delete/", views.TagDeleteView.as_view(), name="tag_delete"),
    # Comments
    path("comments/", views.CommentListView.as_view(), name="comment_list"),
    path(
        "comments/<int:pk>/edit/",
        views.CommentUpdateView.as_view(),
        name="comment_edit",
    ),
    path(
        "comments/<int:pk>/delete/",
        views.CommentDeleteView.as_view(),
        name="comment_delete",
    ),
    # Pages
    path("pages/", views.PageListView.as_view(), name="page_list"),
    path("pages/create/", views.PageCreateView.as_view(), name="page_create"),
    path("pages/<int:pk>/edit/", views.PageUpdateView.as_view(), name="page_edit"),
    path("pages/<int:pk>/delete/", views.PageDeleteView.as_view(), name="page_delete"),
    path("pages/<int:pk>/duplicate/", views.PageDuplicateView.as_view(), name="page_duplicate"),
    # Navigation
    path("navigation/", views.NavigationListView.as_view(), name="navigation_list"),
    path(
        "navigation/create/",
        views.NavigationCreateView.as_view(),
        name="navigation_create",
    ),
    path(
        "navigation/<int:pk>/edit/",
        views.NavigationUpdateView.as_view(),
        name="navigation_edit",
    ),
    path(
        "navigation/<int:pk>/delete/",
        views.NavigationDeleteView.as_view(),
        name="navigation_delete",
    ),
    # FriendLink
    path("friendlinks/", views.FriendLinkListView.as_view(), name="friendlink_list"),
    path(
        "friendlinks/create/",
        views.FriendLinkCreateView.as_view(),
        name="friendlink_create",
    ),
    path(
        "friendlinks/<int:pk>/edit/",
        views.FriendLinkUpdateView.as_view(),
        name="friendlink_edit",
    ),
    path(
        "friendlinks/<int:pk>/delete/",
        views.FriendLinkDeleteView.as_view(),
        name="friendlink_delete",
    ),
    # Users
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/<int:pk>/edit/", views.UserUpdateView.as_view(), name="user_edit"),
    # Settings
    path("settings/", views.SettingsView.as_view(), name="settings"),
    # Debug
    path("debug/", views.DebugDashboardView.as_view(), name="debug"),
    path("debug/mock/", views.DebugMockView.as_view(), name="debug_mock"),
    path("debug/cache/", views.DebugCacheView.as_view(), name="debug_cache"),
    path("debug/email/", views.DebugEmailView.as_view(), name="debug_email"),
    # Bulk Action
    path("bulk-action/<str:model>/", views.BulkActionView.as_view(), name="bulk_action"),
    # Export/Import
    path("export-all/<str:model>/", views.ExportAllView.as_view(), name="export_all"),
    path("import-json/<str:model>/", views.ImportJsonView.as_view(), name="import_json"),
]
