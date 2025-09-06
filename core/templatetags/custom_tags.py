from django import template
import calendar

register = template.Library()


@register.filter
def dict_get(dictionary, key):
    """
    Allows template access like: {{ mydict|dict_get:key }}
    Returns 0 if key is not found (useful for totals).
    """
    if dictionary and key in dictionary:
        return dictionary.get(key)
    return 0


@register.filter
def get_item(dictionary, key):
    """
    Alias for dict_get, so templates using get_item work.
    """
    return dict_get(dictionary, key)


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
def get_month_abbr(month_number):
    """
    Convert month number (1–12) into abbreviated month name.
    Example: 1 → "Jan"
    Useful for pivot table headers.
    """
    try:
        return calendar.month_abbr[int(month_number)]
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
