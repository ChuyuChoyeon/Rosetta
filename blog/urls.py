from django.urls import path
from django.contrib.sitemaps.views import sitemap
from . import views
from .sitemaps import BlogPageSitemap, BlogCategorySitemap, BlogStaticSitemap

app_name = 'blog'

sitemaps = {
    'posts': BlogPageSitemap,
    'categories': BlogCategorySitemap,
    'static': BlogStaticSitemap,
}

urlpatterns = [
    path('', views.BlogIndexView.as_view(), name='index'),
    path('post/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('category/<slug:slug>/', views.BlogCategoryView.as_view(), name='category'),
    path('tag/<slug:tag>/', views.BlogTagView.as_view(), name='tag'),
    path('search/', views.BlogSearchView.as_view(), name='search'),
    path('feed/rss/', views.BlogRSSFeed(), name='rss_feed'),
    path('feed/atom/', views.BlogAtomFeed(), name='atom_feed'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('archive/', views.BlogArchiveIndexView.as_view(), name='archive'),
    path('archive/<int:year>/<int:month>/', views.BlogMonthArchiveView.as_view(), name='month_archive'),
]