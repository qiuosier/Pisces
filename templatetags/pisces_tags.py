import imp


import json
from django import template

register = template.Library()

@register.filter
def format_json(value):
    return json.dumps(value, indent=2)
