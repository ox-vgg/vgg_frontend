from django.conf import settings
from django.shortcuts import render
from django.views.decorators.http import require_GET

@require_GET
def page_not_found(request):
    """ Customized handler for 404 errors, with the intention of taking into account
        site prefix and possible redirections.
        Arguments:
               request: only used to extract meta information
    """
    home_location = settings.SITE_PREFIX + '/'
    if 'HTTP_X_FORWARDED_HOST' in request.META:
        home_location = 'http://' + request.META['HTTP_X_FORWARDED_HOST'] + home_location
    context = {
    'SITE_PREFIX': settings.SITE_PREFIX,
    'HOME_LOCATION': home_location,
    }
    response = render(request, template_name='404.html', context=context)
    response.status_code = 404
    return response
