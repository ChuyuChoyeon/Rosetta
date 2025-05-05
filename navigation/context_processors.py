from .models import NavigationItem

def navigation(request):
    """将导航项添加到模板上下文中"""
    # 只获取顶级菜单项（没有父级的项）
    main_nav_items = NavigationItem.objects.filter(is_active=True, parent__isnull=True).order_by('order')
    
    # 为每个顶级菜单项获取其子项
    for item in main_nav_items:
        item.sub_items = NavigationItem.objects.filter(is_active=True, parent=item).order_by('order')
    
    return {
        'main_navigation': main_nav_items,
    }
