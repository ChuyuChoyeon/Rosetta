from django.urls import path
from . import views

app_name = "administration"

urlpatterns = [
    # --- Dashboard Home ---
    # 管理后台首页
    path("", views.IndexView.as_view(), name="index"),
    
    # --- Content Management (内容管理) ---
    # 文章管理 (Posts)
    path("posts/", views.PostListView.as_view(), name="post_list"),
    path("posts/create/", views.PostCreateView.as_view(), name="post_create"),
    path("posts/<int:pk>/edit/", views.PostUpdateView.as_view(), name="post_edit"),
    path("posts/<int:pk>/delete/", views.PostDeleteView.as_view(), name="post_delete"),
    path("posts/<int:pk>/duplicate/", views.PostDuplicateView.as_view(), name="post_duplicate"),
    
    # 分类管理 (Categories)
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
    path("categories/export/", views.CategoryExportView.as_view(), name="category_export"),
    path("categories/import/", views.CategoryImportView.as_view(), name="category_import"),
    
    # 标签管理 (Tags)
    path("tags/", views.TagListView.as_view(), name="tag_list"),
    path("tags/create/", views.TagCreateView.as_view(), name="tag_create"),
    path("tags/<int:pk>/edit/", views.TagUpdateView.as_view(), name="tag_edit"),
    path("tags/<int:pk>/delete/", views.TagDeleteView.as_view(), name="tag_delete"),
    path("tags/autocomplete/", views.TagAutocompleteView.as_view(), name="tag_autocomplete"),
    
    # 评论管理 (Comments)
    path("comments/", views.CommentListView.as_view(), name="comment_list"),
    path(
        "comments/<int:pk>/edit/",
        views.CommentUpdateView.as_view(),
        name="comment_edit",
    ),
    path(
        "comments/<int:pk>/reply/",
        views.CommentReplyView.as_view(),
        name="comment_reply",
    ),
    path(
        "comments/<int:pk>/delete/",
        views.CommentDeleteView.as_view(),
        name="comment_delete",
    ),
    
    # 单页面管理 (Pages)
    path("pages/", views.PageListView.as_view(), name="page_list"),
    path("pages/create/", views.PageCreateView.as_view(), name="page_create"),
    path("pages/<int:pk>/edit/", views.PageUpdateView.as_view(), name="page_edit"),
    path("pages/<int:pk>/delete/", views.PageDeleteView.as_view(), name="page_delete"),
    path("pages/<int:pk>/duplicate/", views.PageDuplicateView.as_view(), name="page_duplicate"),
    
    # --- Appearance & Settings (外观与设置) ---
    # 导航菜单管理 (Navigation)
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
    path("navigation/export/", views.NavigationExportView.as_view(), name="navigation_export"),
    path("navigation/import/", views.NavigationImportView.as_view(), name="navigation_import"),
    
    # 友情链接管理 (FriendLinks)
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
    path("friendlinks/export/", views.FriendLinkExportView.as_view(), name="friendlink_export"),
    path("friendlinks/import/", views.FriendLinkImportView.as_view(), name="friendlink_import"),

    # 搜索占位符管理 (Search Placeholders)
    path("placeholders/", views.SearchPlaceholderListView.as_view(), name="searchplaceholder_list"),
    path(
        "placeholders/create/",
        views.SearchPlaceholderCreateView.as_view(),
        name="searchplaceholder_create",
    ),
    path(
        "placeholders/<int:pk>/edit/",
        views.SearchPlaceholderUpdateView.as_view(),
        name="searchplaceholder_edit",
    ),
    path(
        "placeholders/<int:pk>/delete/",
        views.SearchPlaceholderDeleteView.as_view(),
        name="searchplaceholder_delete",
    ),
    path("placeholders/export/", views.SearchPlaceholderExportView.as_view(), name="searchplaceholder_export"),
    path("placeholders/import/", views.SearchPlaceholderImportView.as_view(), name="searchplaceholder_import"),
    
    # --- User Management (用户管理) ---
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/create/", views.UserCreateView.as_view(), name="user_create"),
    path("users/<int:pk>/edit/", views.UserUpdateView.as_view(), name="user_edit"),
    path("users/<int:pk>/delete/", views.UserDeleteView.as_view(), name="user_delete"),
    path("users/export/", views.UserExportView.as_view(), name="user_export"),
    path("users/import/", views.UserImportView.as_view(), name="user_import"),
    
    # 用户称号管理 (User Titles)
    path("titles/", views.UserTitleListView.as_view(), name="usertitle_list"),
    path("titles/create/", views.UserTitleCreateView.as_view(), name="usertitle_create"),
    path("titles/<int:pk>/edit/", views.UserTitleUpdateView.as_view(), name="usertitle_edit"),
    path("titles/<int:pk>/delete/", views.UserTitleDeleteView.as_view(), name="usertitle_delete"),
    path("titles/export/", views.UserTitleExportView.as_view(), name="usertitle_export"),
    path("titles/import/", views.UserTitleImportView.as_view(), name="usertitle_import"),

    # 用户组管理 (Groups)
    path("groups/", views.GroupListView.as_view(), name="group_list"),
    path("groups/create/", views.GroupCreateView.as_view(), name="group_create"),
    path("groups/<int:pk>/edit/", views.GroupUpdateView.as_view(), name="group_edit"),
    path("groups/<int:pk>/delete/", views.GroupDeleteView.as_view(), name="group_delete"),
    path("groups/export/", views.GroupExportView.as_view(), name="group_export"),
    path("groups/import/", views.GroupImportView.as_view(), name="group_import"),

    # --- Logs & Audit (日志与审计) ---
    # 操作日志 (Admin LogEntry)
    path("logs/audit/", views.LogEntryListView.as_view(), name="logentry_list"),
    path("logs/audit/<int:pk>/delete/", views.LogEntryDeleteView.as_view(), name="logentry_delete"),
    path("logs/audit/export/", views.LogEntryExportView.as_view(), name="logentry_export"),
    
    # 系统日志 (File Logs)
    path("logs/system/", views.LogFileListView.as_view(), name="logfile_list"),
    path("logs/system/<str:filename>/", views.LogFileView.as_view(), name="logfile_detail"),
    path("logs/system/<str:filename>/download/", views.LogFileDownloadView.as_view(), name="logfile_download"),
    path("logs/system/<str:filename>/delete/", views.LogFileDeleteView.as_view(), name="logfile_delete"),
    
    # --- System Tools (系统工具) ---
    # 系统设置 (Settings - Placeholder)
    path("settings/", views.SettingsView.as_view(), name="settings"),
    
    # 调试工具 (Debug)
    path("debug/", views.DebugDashboardView.as_view(), name="debug"),
    path("debug/ui-test/", views.DebugUITestView.as_view(), name="debug_ui_test"),
    path("debug/permission/", views.DebugPermissionView.as_view(), name="debug_permission"),
    path("debug/mock/", views.DebugMockView.as_view(), name="debug_mock"),
    path("debug/cache/", views.DebugCacheView.as_view(), name="debug_cache"),
    path("debug/email/", views.DebugEmailView.as_view(), name="debug_email"),
    
    # 批量操作 (Bulk Actions)
    path("bulk-action/<str:model>/", views.BulkActionView.as_view(), name="bulk_action"),
    
    # 数据导入导出 (Import/Export)
    path("export-all/<str:model>/", views.ExportAllView.as_view(), name="export_all"),
    path("import-json/<str:model>/", views.ImportJsonView.as_view(), name="import_json"),
]
