from django import template

register = template.Library()


@register.filter
def modulo(value, arg):
    """
    取模运算过滤器
    
    用法: {{ value|modulo:arg }}
    示例: 判断循环索引是否能被 3 整除 {% if forloop.counter|modulo:3 == 0 %}
    """
    return int(value) % int(arg)
