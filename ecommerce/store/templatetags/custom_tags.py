from django import template

register = template.Library()

@register.filter
def index_of(list_, value):
    """
    Returns the index of value in the list.
    """
    try:
        return list_.index(value)
    except ValueError:
        return -1
