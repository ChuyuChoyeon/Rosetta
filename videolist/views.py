from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import VideoSite
from datetime import datetime
import json

def index(request):
    sites = VideoSite.objects.filter(is_invalid=False)
    return render(request, 'videolist/index.html', {'sites': sites})

def import_json(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            success_count = 0
            
            for site in data:
                # 清理 URL 中的反引号
                url = site['url'].strip().replace('`', '').strip()
                # 转换日期格式
                update_time = datetime.strptime(site['updateDate'], '%Y/%m/%d')
                
                # 使用 get_or_create 来避免重复
                obj, created = VideoSite.objects.get_or_create(
                    name=site['name'],
                    defaults={
                        'url': url,
                        'description': site['description'],
                        'update_time': update_time,
                        'is_invalid': False
                    }
                )
                
                if not created:
                    # 更新现有记录
                    obj.url = url
                    obj.description = site['description']
                    obj.update_time = update_time
                    obj.save()
                
                success_count += 1
            
            return JsonResponse({
                'status': 'success',
                'message': f'成功导入 {success_count} 条记录',
                'count': success_count
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': '只支持 POST 请求'
    }, status=405)

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

def import_page(request):
    return render(request, 'videolist/import.html')

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
