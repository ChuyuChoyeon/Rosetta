from django.urls import path
from . import views

app_name = 'videolist'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/sites/', views.site_list, name='site_list'),
    path('sitemap/', views.sitemap, name='sitemap'),
    path('site/<int:site_id>/', views.site_detail, name='site_detail'),
    path('api/import-json/', views.import_json, name='import_json'),
]