from django.urls import path
from . import views

app_name = 'videolist'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/sites/', views.site_list, name='site_list'),
    path('sitemap/', views.sitemap, name='sitemap'),
    path('site/<int:site_id>/', views.site_detail, name='site_detail'),
    path('sites/<int:site_id>/', views.views_count, name='views_count'),
    path('add/', views.add_video_template, name='add_video_template'),
    path('add/video/', views.add_video, name='add_video'),
]