from django.conf import settings
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required

import sys
import os

# add 'controllers' to the path so that we can import stuff from it
sys.path.append(os.path.join(settings.BASE_DIR, 'siteroot', 'controllers'))

# imports from the 'controllers'
import retengine.engine

class AdminPages:
    """
        This class provides rendering services for the pages that can be accessed by an admin user
        Members:
            visor_controller: an instance of the visor backend interface controller
    """

    def __init__(self, visor_controller):
        """
            Initializes an instance of this class
            Arguments:
                visor_controller: an instance of the visor backend interface controller
        """
        self.visor_controller = visor_controller

    @method_decorator(csrf_protect)
    @method_decorator(require_GET)
    @method_decorator(login_required)
    def admintools(self, request):
        """
            Renders the admin tools web page.
            Only GET requests are allowed. This method is CSRF protected to protect the POST triggered
            when saving changes to the configuration.
            Requires user authentication as admin.
            Arguments:
               request: request object containing details of the user session
            Returns:
               HTTP 200 if the page is successfully rendered
        """
        # get all current settings from the options, to fill out the controls in the page
        num_pos_train = self.visor_controller.proc_opts.imsearchtools_opts['num_pos_train']
        improc_timeout = self.visor_controller.proc_opts.imsearchtools_opts['improc_timeout']
        improc_engine_list = ['google_web']
        improc_engine = self.visor_controller.proc_opts.imsearchtools_opts['engine']

        disable_cache = self.visor_controller.proc_opts.disable_cache

        cached_text_queries = self.visor_controller.interface.get_cached_text_queries(user_ses_id=request.session.session_key)
        engines_names = {}
        for engine in cached_text_queries.keys():
            engines_names[engine] = self.visor_controller.opts.engines_dict[engine]['full_name']

        # compute home location taking account any possible redirections
        home_location = settings.SITE_PREFIX + '/'
        if 'HTTP_X_FORWARDED_HOST' in request.META:
            home_location = 'http://' + request.META['HTTP_X_FORWARDED_HOST'] + home_location

        # check if the following settings are specified or not
        dir_settings = dir(settings)
        MAX_TOTAL_SIZE_UPLOAD_INDIVIDUAL_FILES = None
        MAX_NUMBER_UPLOAD_INDIVIDUAL_FILES = None
        VALID_IMG_EXTENSIONS_STR = ''
        if 'MAX_TOTAL_SIZE_UPLOAD_INDIVIDUAL_FILES' in dir_settings:
            MAX_TOTAL_SIZE_UPLOAD_INDIVIDUAL_FILES = settings.MAX_TOTAL_SIZE_UPLOAD_INDIVIDUAL_FILES
        if 'MAX_NUMBER_UPLOAD_INDIVIDUAL_FILES' in dir_settings:
            MAX_NUMBER_UPLOAD_INDIVIDUAL_FILES = settings.MAX_NUMBER_UPLOAD_INDIVIDUAL_FILES
        if 'VALID_IMG_EXTENSIONS_STR' in dir_settings:
            VALID_IMG_EXTENSIONS_STR = settings.VALID_IMG_EXTENSIONS_STR + ", .txt" # accept .txt too for providing list of files

        engines_with_pipeline = {}
        for engine in settings.VISOR['engines']:
            if 'data_manager_module' in settings.VISOR['engines'][engine]:
                engines_with_pipeline[engine] = settings.VISOR['engines'][engine]['full_name']

        # set up rendering context and render the page
        context = {
        'HOME_LOCATION': home_location,
        'SITE_TITLE': settings.VISOR['title'],
        'NUM_POS_TRAIN': num_pos_train,
        'DISABLE_CACHE': disable_cache,
        'IMPROC_TIMEOUT' : improc_timeout,
        'IMPROC_ENGINE' : improc_engine,
        'IMPROC_ENGINE_LIST' : improc_engine_list,
        'ENGINES_NAMES': engines_names,
        'ENGINES_WITH_PIPELINE': engines_with_pipeline,
        'CACHED_TEXT_QUERIES' : cached_text_queries,
        'MAX_TOTAL_SIZE_UPLOAD_INDIVIDUAL_FILES': MAX_TOTAL_SIZE_UPLOAD_INDIVIDUAL_FILES,
        'MAX_NUMBER_UPLOAD_INDIVIDUAL_FILES': MAX_NUMBER_UPLOAD_INDIVIDUAL_FILES,
        'VALID_IMG_EXTENSIONS_STR': VALID_IMG_EXTENSIONS_STR
        }
        return render(request, "admintools.html", context)

