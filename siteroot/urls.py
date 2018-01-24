from django.conf.urls import url
from django.contrib import admin
from django.conf import settings

# import main class intances
from mains import user_pages, admin_pages, api_functions

urlpatterns = [

    # User pages

    url(r'^$', user_pages.site_index, name='index'),
    url(r'^searchproc_qstr$', user_pages.search_process, name='search_process'),
    url(r'^waitforit$', user_pages.waitforit_process, name='wait_for_it'),
    url(r'^searchres$', user_pages.searchres, name='searchres'),
    url(r'^searchreslist$', user_pages.searchreslist, name='searchreslist'),
    url(r'^searchresroislist$', user_pages.searchresroislist, name='searchresroislist'),
    url(r'^viewdetails$', user_pages.viewdetails, name='viewdetails'),
    url(r'^trainingimages$', user_pages.get_trainingimages, name='trainingimages'),
    url(r'^nobackend', user_pages.nobackend, name='nobackend'),
    url(r'^accounts/profile/$', user_pages.user_profile, name='user_profile'),
    url(r'^selectpageimages$', user_pages.selectpageimages, name='selectpageimages'),

    # Admin pages (requires user authentication)

    url(r'^admin/', admin.site.urls),
    url(r'^admintools', admin_pages.admintools, name='admintools'),

    # Authentication

    url(r'^login/$', user_pages.login, name='login'),
    url(r'^logout/$', user_pages.logout, name='logout'),

    # API urls (public)

    url(r'^save_uber_classifier$', api_functions.save_uber_classifier, name='save_uber_classifier'),
    url(r'^is_backend_reachable', api_functions.get_backend_reachable, name='backendreachable'),
    url(r'^execquery$', api_functions.exec_query, name='exec_query'),
    url(r'^uploadimage$', api_functions.upload_image, name='uploadimage'),
    url(r'^(?P<img_set>thumbnails|datasets|postrainimgs|curatedtrainimgs|uploadedimgs|regions)/(.*/)', api_functions.get_image, name='getimage'),
    url(r'^text_suggestions', api_functions.get_text_suggestions, name='text_suggestions'),
    url(r'^savelistastext$', api_functions.savelistastext, name='savelistastext'),

    # API urls (restricted - requires user authentication)

    url(r'^set_config$', api_functions.set_config, name='set_config'),
    url(r'^delete_text_query$', api_functions.delete_text_query, name='delete_text_query'),
    url(r'^clear_cache$', api_functions.clear_cache, name='clear_cache'),
    url(r'^pipeline_input$', api_functions.pipeline_input, name='pipeline_input'),
    url(r'^pipeline_input_status$', api_functions.pipeline_input_status, name='pipeline_input_status'),
    url(r'^pipeline_start$', api_functions.pipeline_start, name='pipeline_start'),
    url(r'^pipeline_status$', api_functions.pipeline_status, name='pipeline_status'),
    url(r'^start_backend$', api_functions.start_backend, name='start_backend'),
    url(r'^stop_backend$', api_functions.stop_backend, name='stop_backend'),
    url(r'^clear_backend$', api_functions.clear_backend, name='clear_backend'),

]
