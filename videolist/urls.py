from django.urls import path
from . import views

app_name = 'videolist'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/sites/', views.site_list, name='site_list'),
    path('import-page/', views.import_page, name='import_page'),
    path('import/', views.import_json, name='import_json'),
]