from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from .models import VideoSite
import json
from datetime import datetime
from functools import wraps
from asgiref.sync import sync_to_async
from django.template.loader import render_to_string


def async_view(view_func):
    """自定义装饰器：将视图转换为异步兼容模式"""
    @wraps(view_func)
    async def wrapper(request, *args, **kwargs):
        return await view_func(request, *args, **kwargs)
    return wrapper


@async_view
async def index(request):
    """首页视图，展示所有有效的视频站点"""
    # 使用 sync_to_async 将 ORM 查询转换为异步操作
    sites = await sync_to_async(list)(VideoSite.objects.filter(is_invalid=False))
    
    # 使用异步安全的方式渲染模板
    context = {'sites': sites}
    
    # 异步版本的render函数
    html_content = await sync_to_async(render_to_string)(
        'videolist/index.html', 
        context=context, 
        request=request
    )
    return HttpResponse(html_content)


@async_view
async def site_list(request):
    """站点列表 API，可按分类过滤"""
    category = request.GET.get('category', None)
    
    # 构建查询
    query = VideoSite.objects.filter(is_invalid=False)
    if category:
        query = query.filter(category=category)
    
    # 异步获取查询结果
    sites = await sync_to_async(list)(query)
    
    # 格式化数据
    data = [{
        'id': site.id,
        'name': site.name,
        'url': site.url,
        'description': site.description,
        'update_time': site.update_time.strftime('%Y-%m-%d %H:%M:%S'),
        'category': site.get_category_display()
    } for site in sites]
    
    return JsonResponse(data, safe=False)


@async_view
async def sitemap(request):
    """网站地图视图，展示所有有效的视频站点"""
    # 异步获取不同分类的视频站点
    movie_sites = await sync_to_async(list)(
        VideoSite.objects.filter(is_invalid=False, category='movie').order_by('name')
    )
    
    anime_sites = await sync_to_async(list)(
        VideoSite.objects.filter(is_invalid=False, category='anime').order_by('name')
    )
    
    context = {
        'movie_sites': movie_sites,
        'anime_sites': anime_sites,
    }
    
    # 异步版本的render函数
    html_content = await sync_to_async(render_to_string)(
        'videolist/sitemap.html', 
        context=context, 
        request=request
    )
    return HttpResponse(html_content)


# 将 get_object_or_404 函数转换为异步版本
async def get_object_or_404_async(klass, *args, **kwargs):
    """异步版本的 get_object_or_404"""
    # 先通过同步方式在同步线程中尝试获取对象
    result = await sync_to_async(get_object_or_404_sync)(klass, *args, **kwargs)
    return result

def get_object_or_404_sync(klass, *args, **kwargs):
    """同步版本的 get_object_or_404，用于在异步函数中通过sync_to_async调用"""
    from django.shortcuts import get_object_or_404
    return get_object_or_404(klass, *args, **kwargs)


@async_view
async def site_detail(request, site_id):
    """单个视频站点的详情页面"""
    # 获取站点详情
    site = await get_object_or_404_async(VideoSite, id=site_id, is_invalid=False)
    
    # 获取推荐站点
    related_sites = await sync_to_async(list)(
        VideoSite.objects.filter(
            category=site.category, 
            is_invalid=False
        ).exclude(id=site.id)[:5]
    )
    
    context = {
        'site': site,
        'related_sites': related_sites,
    }
    
    # 异步版本的render函数
    html_content = await sync_to_async(render_to_string)(
        'videolist/site_detail.html', 
        context=context, 
        request=request
    )
    return HttpResponse(html_content)


@require_http_methods(["POST"])
@async_view
async def import_json(request):
    """导入JSON数据的视图"""
    try:
        # 解析请求体的JSON数据
        data = json.loads(request.body)
        
        if not isinstance(data, list):
            return JsonResponse({'error': '数据必须是列表格式'}, status=400)
        
        result = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }
        
        # 处理每个站点数据
        for site_data in data:
            try:
                # 确保必要的字段存在
                if 'name' not in site_data:
                    result['errors'].append(f"站点缺少名称字段: {site_data}")
                    result['skipped'] += 1
                    continue
                    
                if 'url' not in site_data:
                    result['errors'].append(f"站点缺少URL字段: {site_data}")
                    result['skipped'] += 1
                    continue
                
                # 根据名称查询是否存在
                name = site_data['name']
                site = await sync_to_async(
                    lambda: VideoSite.objects.filter(name=name).first()
                )()
                
                # 处理更新日期
                update_date = None
                if 'updateDate' in site_data:
                    try:
                        update_date = datetime.strptime(site_data['updateDate'], '%Y/%m/%d')
                    except ValueError:
                        # 尝试其他日期格式
                        try:
                            update_date = datetime.strptime(site_data['updateDate'], '%Y-%m-%d')
                        except ValueError:
                            result['errors'].append(f"无效的日期格式: {site_data['updateDate']}")
                
                # 准备站点数据
                site_values = {
                    'url': site_data['url'],
                    'description': site_data.get('description', ''),
                }
                
                # 仅在新建站点时设置分类，更新时保留原有分类
                if 'category' in site_data and not site:
                    site_values['category'] = site_data['category']
                
                if site:
                    # 更新现有站点
                    await sync_to_async(
                        lambda: VideoSite.objects.filter(id=site.id).update(**site_values)
                    )()
                    result['updated'] += 1
                else:
                    # 创建新站点
                    if 'category' not in site_values:
                        site_values['category'] = 'movie'  # 默认分类
                        
                    # 创建站点
                    await sync_to_async(
                        lambda: VideoSite.objects.create(name=name, **site_values)
                    )()
                    result['created'] += 1
                    
            except Exception as e:
                result['errors'].append(f"处理站点时出错: {str(e)}")
                result['skipped'] += 1
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON格式无效'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
