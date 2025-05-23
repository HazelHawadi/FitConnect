from django import template

register = template.Library()

@register.filter
def range_filter(value):
    try:
        return range(int(value))
    except (ValueError, TypeError):
        return []

@register.filter(name='add_class')
def add_class(value, arg):
    return value.as_widget(attrs={'class': arg})