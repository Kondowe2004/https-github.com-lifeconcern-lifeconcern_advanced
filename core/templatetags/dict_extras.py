import calendar
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if dictionary is None:
        return ''
    try:
        return dictionary.get(key, '')
    except Exception:
        return ''

@register.filter
def get_month_name(value):
    """Convert month number (1–12) to short month name."""
    try:
        return calendar.month_abbr[int(value)]
    except Exception:
        return value
