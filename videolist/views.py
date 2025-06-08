from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import VideoSite, SiteView
import json
from datetime import datetime
from functools import wraps
from asgiref.sync import sync_to_async


def async_view(view_func):
    @wraps(view_func)
    async def wrapper(request, *args, **kwargs):
        return await view_func(request, *args, **kwargs)
    return wrapper



def index(request):
    """首页视图，展示所有有效的视频站点"""
    # 使用 sync_to_async 将 ORM 查询转换为异步操作
    sites = list(VideoSite.objects.filter(is_invalid=False))
    visit_count = SiteView.objects.count() 
    # 使用异步安全的方式渲染模板.
    
    context = {'sites': sites,'visit_count':visit_count}
    
    # 记录访问ip和用户代理
    SiteView.objects.create(
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )
    
    # 异步版本的render函数
    return render(request, 'videolist/index.html', context)


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
        'view_count' : site.view_count,
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
    return await sync_to_async(render)(request, 'videolist/sitemap.html', context)



async def get_object_or_404_async(klass, *args, **kwargs):
    """异步版本的 get_object_or_404"""
    result = await sync_to_async(get_object_or_404)(klass, *args, **kwargs)
    return result

def get_object_or_404_sync(klass, *args, **kwargs):
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
    return await sync_to_async(render)(request, 'videolist/site_detail.html', context)


def views_count(request, site_id):
    """记录视频站点的浏览次数"""
    video = VideoSite.objects.filter(id=site_id)[0]
    # 获取或创建浏览记录
    video.view_count += 1
    video.save(update_fields=['view_count'])
    
    return JsonResponse({'view_count': '站点浏览次数已更新'})





# 增加添加视频 链接功能
def add_video(request):
    """添加视频站点的视图"""
    if request.method == 'POST':
        data = request.POST
        print('data:', data)
        name = data.get('name')
        url = data.get('url')
        description = data.get('description', '')
        category = data.get('category', 'movie')
        update_time = datetime.now()
        
        # 创建新的视频站点
        new_site = VideoSite.objects.create(
            name=name,
            url=url,
            description=description,
            category=category,
            is_invalid=True,
            update_time=update_time
        )
        # 返回新站点的详细信息
        response_data = {
            'id': new_site.id,
            'name': new_site.name,
            'url': new_site.url,
            'description': new_site.description,
            'update_time': new_site.update_time.strftime('%Y-%m-%d %H:%M:%S'),
            'view_count': new_site.view_count,
            'category': new_site.get_category_display()
        }
        return render(request, 'videolist/add_site.html', {'code': 200, 'info': "添加成功", 'site': response_data})
    else:
        # 如果不是 POST 请求，返回错误信息
        return render(request, 'videolist/add_site.html', {'code' : 400,'info': '添加失败'})
    


#  增加添加视频 链接功能的模板视图

def add_video_template(request):
    """添加视频站点的模板视图"""
    return  render(request, 'videolist/add_site.html')