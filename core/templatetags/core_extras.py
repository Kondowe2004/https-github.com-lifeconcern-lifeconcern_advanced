from django import template
register = template.Library()

@register.filter
def dict_get(grid, pair):
    # not used; leaving for future
    return None
