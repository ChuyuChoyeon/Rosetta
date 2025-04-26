from django.shortcuts import render
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
