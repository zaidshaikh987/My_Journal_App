from django import template
from urllib.parse import urlencode, parse_qs, urlparse, urlunparse

register = template.Library()

@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """
    Replace or add URL parameters in the current URL.
    
    Usage in template:
    <a href="?{% url_replace page=page_obj.next_page_number %}">Next</a>
    """
    request = context['request']
    query_params = request.GET.copy()
    
    for key, value in kwargs.items():
        if value is not None and value != '':
            query_params[key] = value
        elif key in query_params:
            del query_params[key]
    
    return query_params.urlencode()
