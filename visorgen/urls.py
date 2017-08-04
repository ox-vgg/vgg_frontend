"""visorgen URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.views.generic import RedirectView

SITE_PREFIX = settings.SITE_PREFIX.replace('/','') # make sure to avoid any extra /

urlpatterns = [
    url(r'^%s/admin/' % SITE_PREFIX, admin.site.urls),
    url(r'^%s/' % SITE_PREFIX , include('siteroot.urls')),
    url(r'^$', RedirectView.as_view(url='%s/' % SITE_PREFIX, permanent=False)),
]

# override 404 handler to show customised page
handler404 = 'siteroot.views.errors.page_not_found'
