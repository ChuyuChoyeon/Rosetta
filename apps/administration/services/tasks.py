from celery import current_app
from django.conf import settings
import inspect
from django.utils.translation import gettext as _

def get_registered_tasks():
    """
    获取所有已注册的 Celery 任务列表。
    返回一个元组列表 (task_name, task_name) 供 ChoiceField 使用。
    """
    # 确保任务已加载
    current_app.loader.import_default_modules()
    
    tasks = list(sorted(name for name in current_app.tasks
                        if not name.startswith('celery.')))
    
    # 如果需要，过滤掉内部任务或对其进行分类
    choices = []
    for task in tasks:
        choices.append((task, task))
        
    return choices

def get_task_info_map():
    """
    获取任务的详细信息映射，用于前端展示。
    返回: { 'task_name': { 'doc': '...', 'signature': '...' } }
    """
    current_app.loader.import_default_modules()
    
    tasks = list(sorted(name for name in current_app.tasks
                        if not name.startswith('celery.')))
    
    info_map = {}
    for task_name in tasks:
        task = current_app.tasks[task_name]
        doc = (inspect.getdoc(task) or "").strip()
        
        signature = _("未知签名")
        try:
            # 尝试获取 run 方法的签名 (常规任务)
            if hasattr(task, 'run'):
                signature = str(inspect.signature(task.run))
            # 尝试直接获取任务函数的签名
            else:
                signature = str(inspect.signature(task))
        except (AttributeError, ValueError, TypeError):
            pass
            
        info_map[task_name] = {
            "doc": doc,
            "signature": signature
        }
        
    return info_map
