from django import template
from blog.forms import SubscriberForm

register = template.Library()


@register.inclusion_tag("blog/partials/subscribe_form.html")
def subscribe_form():
    """
    渲染订阅表单
    
    用于在侧边栏或页脚插入订阅表单。
    返回包含 SubscriberForm 实例的上下文。
    """
    return {"subscribe_form": SubscriberForm()}


@register.filter
def modulo(value, arg):
    """
    取模运算过滤器
    
    用法: {{ value|modulo:arg }}
    示例: 判断循环索引是否能被 3 整除 {% if forloop.counter|modulo:3 == 0 %}
    """
    return int(value) % int(arg)
