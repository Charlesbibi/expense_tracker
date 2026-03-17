from django import template

register = template.Library()

@register.filter
def add_class(value, arg):
    """为表单字段添加 CSS 类"""
    return value.as_widget(attrs={'class': arg})
