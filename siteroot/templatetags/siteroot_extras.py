from django import template
from django.template.defaultfilters import stringfilter
register = template.Library()

@register.filter
@stringfilter
def intToCommaStr(int_ip):
    """ Simple function to convert an integer to a string with a specific format  """
    import sys
    if sys.version_info < (2, 7):
        return str(int_ip)
    else:
        int_ip = int(int_ip)
        return '{:,d}'.format(int_ip)

@register.filter
@stringfilter
def trunc(s, max_pos=75):
    """ Simple function to truncate a string  """    
    length = len(s)
    if length <= max_pos:
        return s
    else:
        end = s.rfind(' ',0,max_pos)
        if end > 0 and end > max_pos-5:
            return s[0:end] + '...'
        else:
            if s[max_pos-1] == '.':
                max_pos = max_pos - 1
            return s[0:max_pos] + '...'

