from django import template
import base64

register = template.Library()

@register.filter
def base64encode(value):
    """Encode image to base64"""
    return base64.b64encode(value.getvalue()).decode('utf-8')
