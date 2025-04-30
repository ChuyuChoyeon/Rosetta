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
            request_data = json.loads(request.body)
            
            # 从请求中获取数据和键映射配置
            if isinstance(request_data, list):
                # 兼容旧版格式，整个请求体就是数据数组
                data = request_data
                category = 'movie'  # 默认分类
                key_mapping = {
                    'nameKey': 'name',
                    'urlKey': 'url',
                    'descriptionKey': 'description',
                    'updateDateKey': 'updateDate',
                    'dateFormat': '%Y/%m/%d'
                }
            else:
                # 新版格式，请求体包含数据、分类和键映射
                data = request_data.get('data', [])
                category = request_data.get('category', 'movie')
                key_mapping = request_data.get('keyMapping', {
                    'nameKey': 'name',
                    'urlKey': 'url',
                    'descriptionKey': 'description',
                    'updateDateKey': 'updateDate',
                    'dateFormat': '%Y/%m/%d'
                })
            
            # 提取键名
            name_key = key_mapping.get('nameKey', 'name')
            url_key = key_mapping.get('urlKey', 'url')
            description_key = key_mapping.get('descriptionKey', 'description')
            update_date_key = key_mapping.get('updateDateKey', 'updateDate')
            date_format = key_mapping.get('dateFormat', '%Y/%m/%d')
            
            success_count = 0
            error_items = []
            
            for site in data:
                try:
                    # 确保所有必需的字段都存在
                    if not all(k in site for k in [name_key, url_key, description_key, update_date_key]):
                        error_items.append(f"缺少必需字段: {site.get(name_key, '未知站点')}")
                        continue
                    
                    # 清理 URL 中的反引号
                    url = site[url_key].strip().replace('`', '').strip()
                    
                    # 转换日期格式
                    try:
                        update_time = datetime.strptime(site[update_date_key], date_format)
                    except ValueError:
                        error_items.append(f"日期格式错误: {site[update_date_key]} (期望格式: {date_format})")
                        continue
                    
                    # 获取分类，如果没有提供则使用默认值
                    site_category = site.get('category', category)
                    if site_category not in dict(VideoSite.CATEGORY_CHOICES):
                        site_category = category  # 如果分类无效，使用默认值
                    
                    # 使用 get_or_create 来避免重复
                    obj, created = VideoSite.objects.get_or_create(
                        name=site[name_key],
                        defaults={
                            'url': url,
                            'description': site[description_key],
                            'update_time': update_time,
                            'is_invalid': False,
                            'category': site_category
                        }
                    )
                    
                    if not created:
                        # 更新现有记录
                        obj.url = url
                        obj.description = site[description_key]
                        obj.update_time = update_time
                        obj.category = site_category
                        obj.save()
                    
                    success_count += 1
                except Exception as item_error:
                    error_items.append(f"处理项目错误: {str(item_error)}")
            
            response_message = f'成功导入 {success_count} 条记录'
            if error_items:
                response_message += f'，有 {len(error_items)} 条记录失败'
            
            return JsonResponse({
                'status': 'success',
                'message': response_message,
                'count': success_count,
                'errors': error_items[:10] if error_items else []  # 只返回前10个错误
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'导入失败: {str(e)}'
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
