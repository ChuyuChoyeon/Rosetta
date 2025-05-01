from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import VideoSite


def index(request):
    sites = VideoSite.objects.filter(is_invalid=False)
    return render(request, 'videolist/index.html', {'sites': sites})
def site_list(request):
    category = request.GET.get('category', None)
    sites = VideoSite.objects.filter(is_invalid=False)
    
    if category:
        sites = sites.filter(category=category)
        
    data = [{
        'id': site.id,
        'name': site.name,
        'url': site.url,
        'description': site.description,
        'update_time': site.update_time.strftime('%Y-%m-%d %H:%M:%S'),
        'category': site.get_category_display()
    } for site in sites]
    return JsonResponse(data, safe=False)


def sitemap(request):
    """网站地图视图，展示所有有效的视频站点"""
    # 获取所有有效的视频站点，按分类分组
    movie_sites = VideoSite.objects.filter(is_invalid=False, category='movie').order_by('name')
    anime_sites = VideoSite.objects.filter(is_invalid=False, category='anime').order_by('name')
    
    context = {
        'movie_sites': movie_sites,
        'anime_sites': anime_sites,
    }
    
    return render(request, 'videolist/sitemap.html', context)

def site_detail(request, site_id):
    """单个视频站点的详情页面"""
    site = get_object_or_404(VideoSite, id=site_id, is_invalid=False)
    
    # 获取相同分类的其他站点推荐
    related_sites = VideoSite.objects.filter(
        category=site.category, 
        is_invalid=False
    ).exclude(id=site.id)[:5]
    
    context = {
        'site': site,
        'related_sites': related_sites,
    }
    
    return render(request, 'videolist/site_detail.html', context)
