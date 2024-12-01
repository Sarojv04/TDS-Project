from django import template

register = template.Library()

@register.filter
def get(dictionary, key):
    """Custom filter to get a value from a dictionary by its key."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def total_sum(values):
    """Return the sum of a list of values."""
    try:
        return sum(values)  # Use Python's built-in sum here
    except TypeError:
        return 0
