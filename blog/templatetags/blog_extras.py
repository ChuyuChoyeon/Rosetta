from django import template
from blog.forms import SubscriberForm

register = template.Library()


@register.inclusion_tag("blog/partials/subscribe_form.html")
def subscribe_form():
    return {"subscribe_form": SubscriberForm()}


@register.filter
def modulo(value, arg):
    return int(value) % int(arg)
