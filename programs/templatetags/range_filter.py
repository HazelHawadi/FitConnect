from django import template

register = template.Library()

@register.filter
def range_filter(value):
    try:
        return range(int(value))
    except (ValueError, TypeError):
        return []
