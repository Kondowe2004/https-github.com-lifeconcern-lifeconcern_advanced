from django import template
import calendar

register = template.Library()


@register.filter
def dict_get(dictionary, key):
    """
    Allows template access like: {{ mydict|get:key }}
    """
    if dictionary and key in dictionary:
        return dictionary.get(key)
    return None


@register.filter
def get_month_name(month_number):
    """
    Convert month number (1–12) into full month name.
    Example: 1 → "January"
    """
    try:
        return calendar.month_name[int(month_number)]
    except (ValueError, TypeError, IndexError):
        return ""


@register.filter
def zip_lists(a, b):
    """
    Zip two lists together for iteration in templates.
    Example:
      {% for x, y in list1|zip_lists:list2 %}
        {{ x }} - {{ y }}
      {% endfor %}
    """
    try:
        return zip(a, b)
    except Exception:
        return []
