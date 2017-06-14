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
        self.visor_controller =  visor_controller

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
        improc_engine_list = [ 'google_web' ]
        improc_engine = self.visor_controller.proc_opts.imsearchtools_opts['engine']

        rqt_objdict = retengine.models.opts.rf_rank_types.__dict__
        rf_rank_type_list = [rqt_objdict[a] for a in rqt_objdict.keys()
                               if not (a.startswith('__') and a.endswith('__'))]
        rf_rank_type = self.visor_controller.proc_opts.rf_rank_type
        rf_rank_topn = self.visor_controller.proc_opts.rf_rank_topn

        rtt_objdict = retengine.models.opts.rf_train_types.__dict__
        rf_train_type_list = [rtt_objdict[a] for a in rtt_objdict.keys()
                               if not (a.startswith('__') and a.endswith('__'))]
        rf_train_type = self.visor_controller.proc_opts.rf_train_type

        disable_cache = self.visor_controller.proc_opts.disable_cache

        cached_text_queries = self.visor_controller.interface.get_cached_text_queries(user_ses_id=request.session.session_key)
        engines_names = {}
        for engine in cached_text_queries.keys():
            engines_names[engine] = self.visor_controller.opts.engines_dict[engine]['full_name']

        # compute home location taking account any possible redirections
        home_location = settings.SITE_PREFIX + '/'
        if 'HTTP_X_FORWARDED_HOST' in request.META:
            home_location = request.META['UWSGI_SCHEME'] + '://' + request.META['HTTP_X_FORWARDED_HOST'] + home_location

        # set up rendering context and render the page
        context = {
        'HOME_LOCATION': home_location,
        'SITE_TITLE': settings.VISOR['title'],
        'NUM_POS_TRAIN': num_pos_train,
        'DISABLE_CACHE': disable_cache,
        'IMPROC_TIMEOUT' : improc_timeout,
        'IMPROC_ENGINE' : improc_engine,
        'IMPROC_ENGINE_LIST' : improc_engine_list,
        'RF_RANK_TYPE' : rf_rank_type,
        'RF_RANK_TYPE_LIST' : rf_rank_type_list,
        'RF_RANK_TOPN' : rf_rank_topn,
        'RF_TRAIN_TYPE' : rf_train_type,
        'RF_TRAIN_TYPE_LIST' : rf_train_type_list,
        'ENGINES_NAMES': engines_names,
        'CPUVISOR_ENABLED': 'cpuvisor-srv' in engines_names.keys(),
        'CACHED_TEXT_QUERIES' : cached_text_queries
        }
        return render(request, "admintools.html", context)

