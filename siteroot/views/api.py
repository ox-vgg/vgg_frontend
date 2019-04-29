from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, Http404
from django.shortcuts import redirect, render_to_response, render
from django.views.decorators.http import require_GET, require_POST
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

import urllib
import os
import sys
import json
import glob
import threading
import ast
import tempfile

PATH_TO_CAFFE_BACKEND_PROTO = os.path.join(settings.BASE_DIR, '../vgg_classifier/proto')
if os.path.exists(PATH_TO_CAFFE_BACKEND_PROTO):
    from google.protobuf import text_format
    sys.path.append(PATH_TO_CAFFE_BACKEND_PROTO) # add this to be able to load cpuvisor_config_pb2
    import cpuvisor_config_pb2

import retengine.engine.backend_client
import api_globals
sys.path.append(os.path.join(os.path.dirname(__file__), '../../pipeline')) # add this to be able to load all data ingestion pipelines
from data_pipeline_cpuvisor import data_processing_pipeline_cpuvisor
from data_pipeline_faces import data_processing_pipeline_faces

class APIFunctions:
    """
        This class provides general REST methods that complement the user/admin pages
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
        available_engines = self.visor_controller.opts.engines_dict
        self.ENGINES_WITH_PIPELINE = ['cpuvisor-srv', 'faces']

        # init paths to negative/positive dirs
        self.DATASET_IM_BASE_PATH = None
        self.DATASET_IM_PATHS = None
        self.NEGATIVE_IM_PATHS = None
        self.NEGATIVE_IM_BASE_PATH = None
        self.DATASET_FEATS_FILE = None
        self.NEG_FEATS_FILE = None

        # init vars to support the multi-threaded pipeline
        self.threads_map = {}
        self.lock = threading.Lock()
        self.pipeline_frame_list = []
        self.pipeline_video_list = []
        self.total_input_files = None
        self.global_input_index = -1
        self.pipeline_input_type = ''
        self.pipeline_engine = ''

        # init constants for video processing.
        # So far these are only defined here and should
        # not be changed via the settings
        self.num_video_threads = 2
        self.video_chunk_size = 1

        # init vars to support backend service management
        self.backend_thread = None

        # init vars to support pipeline input acquisition
        self.pipeline_input_thread = None


    def get_engine_config(self, engine):
        """
            Retrieves the data ingestion pipeline configuration for the specified engine.
            Arguments:
               engine: Key to the engine in the dictionary of supported engines in the settings
            Returns:
               A tuple with at least the path to the base folder for the image ingestion and the
               names and paths to the holders for the positive feature files. Additionally, it
               can return the names and paths to the holders for the negative feature files.
        """
        if engine == 'cpuvisor-srv':

            # read cpuvisor configuration file
            cpuvisor_config_proto = cpuvisor_config_pb2.Config()
            cpuvisor_config_file = open(settings.CONFIG_PROTO_PATH, "r")
            text_format.Merge(str(cpuvisor_config_file.read()), cpuvisor_config_proto)
            cpuvisor_config_file.close()

            # Get some info from the proto config
            return  (cpuvisor_config_proto.preproc_config.dataset_im_base_path,
            cpuvisor_config_proto.preproc_config.dataset_im_paths,
            cpuvisor_config_proto.preproc_config.neg_im_paths,
            cpuvisor_config_proto.preproc_config.neg_im_base_path,
            cpuvisor_config_proto.preproc_config.dataset_feats_file,
            cpuvisor_config_proto.preproc_config.neg_feats_file)

        if engine == 'faces':

            # Get the info from the settings
            return  (settings.FACE_ENGINE_SETTINGS['FACES_DATASET_IM_BASE_PATH'],
                settings.FACE_ENGINE_SETTINGS['FACES_DATASET_IM_PATHS'],
                settings.FACE_ENGINE_SETTINGS['FACES_NEGATIVE_IM_PATHS'],
                settings.FACE_ENGINE_SETTINGS['FACES_NEGATIVE_IM_BASE_PATH'],
                settings.FACE_ENGINE_SETTINGS['FACES_DATASET_FEATS_FILE'],
                settings.FACE_ENGINE_SETTINGS['FACES_NEG_FEATS_FILE'])


    @method_decorator(require_GET)
    def savelistastext(self, request):
        """
            Saves a specified query as a list of items in plain text
            Only GET requests are allowed.
            Arguments:
               request: request object specifying the id of the query to be saved
            Returns:
               Redirects to a text file in the static area of the site
               HTTP 400 if the query id is missing or something else goes wrong.
        """
        query_id = request.GET.get('qsid', None)

        if query_id == None or len(query_id) == 0:
            return HttpResponseBadRequest("Query ID not specified")

        page = request.GET.get('page', None)
        if page == None  or len(page) == 0:
            return HttpResponseBadRequest("Page not specified")
        page = int(page)

        idx_list = request.GET.get('list', None)
        if idx_list == None or len(idx_list) == 0:
            return HttpResponseBadRequest("List not specified")
        idx_list = idx_list.split(';')
        idx_list = idx_list[:-1]

        try:

            # get query definition dict from query_ses_id
            query = self.visor_controller.query_key_cache.get_query_details(query_id)

            # get query result
            query_data = self.visor_controller.get_query_result(query, request.session.session_key, query_ses_id=query_id)
            rlist = query_data.rlist

            # extract page
            (rlist, page_count) = self.visor_controller.page_manager.get_page(rlist, page)
            if page > page_count:
                return HttpResponseBadRequest("Incorrect page specified")

            # create file using query_id and only the items with indexes included in the idx_list
            with open(os.path.join(os.path.dirname(__file__), '..', 'static', 'lists', '%s_%s.txt' % (query_id, page)), 'w') as fout:
                for idx in idx_list:
                    int_idx = int(idx)
                    fout.write(rlist[int_idx]['path'] + '\n')

            # respond with a redirect
            home_location = settings.SITE_PREFIX + '/'
            if 'HTTP_X_FORWARDED_HOST' in request.META:
                home_location = 'http://' + request.META['HTTP_X_FORWARDED_HOST'] + home_location

            return redirect(home_location + ('static/lists/%s_%s.txt' % (query_id, page)))

        except Exception as e:

            return HttpResponseBadRequest(str(e))


    @method_decorator(require_GET)
    def save_uber_classifier(self, request):
        """
            Saves a specified query as an Uber Classifier
            Only GET requests are allowed.
            Arguments:
               request: request object specifying the id and name of the query to be saved
            Returns:
               HTTP 200 with data=1 if successful, HTTP 200 with data=0 otherwise
               HTTP 400 if the parameters are missing.
               These return values are defined in the searchreslist.html template
        """
        query_id = request.GET.get('qsid', None)
        name = request.GET.get('name', None)

        if query_id == None:
            return HttpResponseBadRequest("Query ID not specified")

        if name == None:
            return HttpResponseBadRequest("Missing name for uber classifier")

        # get query definition dict from query_ses_id
        query = self.visor_controller.query_key_cache.get_query_details(query_id)

        if self.visor_controller.interface.save_uber_classifier(query, name):
            return HttpResponse('1') # success ! as defined in the searchreslist.html template
        else:
            return HttpResponse('0') # failed  ! as defined in the searchreslist.html template


    @method_decorator(require_POST)
    @method_decorator(login_required)
    def set_config(self, request):
        """
            Saves the specified configuration for visor
            Only POST requests are allowed. This method is CSRF protected.
            Requires user authentication, as only admins should be allowed to execute it.
            Arguments:
               request: request object specifying a map with all the configuration settings
            Returns:
               reloads the admintools page if successful. It should trigger an exception otherwise
        """
        self.visor_controller.set_config(request.POST, request.session.session_key)
        return redirect('admintools')


    @method_decorator(require_GET)
    @method_decorator(login_required)
    def clear_cache(self, request):
        """
            Clears out a cache folder from the site data
            Only GET requests are allowed.
            Requires user authentication, as only admins should be allowed to execute it.
            Arguments:
               request: request object specifying the cache type to be cleared
            Returns:
               HTTP 200 if successful, HTTP 400 if the cache type is not specified.
        """
        cache_type = request.GET.get('type', None)
        if cache_type == None:
            return HttpResponseBadRequest("Cache type not specified")

        self.visor_controller.interface.clear_cache(cache_type)
        self.visor_controller.query_key_cache.clear_all_sessions()
        return HttpResponse()


    @method_decorator(require_GET)
    @method_decorator(login_required)
    def delete_text_query(self, request):
        """
            Removes the information held for a specific text query
            Only GET requests are allowed.
            Requires user authentication, as only admins should be allowed to execute it.
            Arguments:
               request: request object specifying the id of the query to be executed
            Returns:
               HTTP 200 if successful. HTTP 400 if the query text is missing.
        """
        query_text = request.GET.get('q', None)
        engine = request.GET.get('engine', None)
        if query_text == None or engine == None:
            return HttpResponseBadRequest("Query text not correctly specified or query does not exist")

        self.visor_controller.query_key_cache.delete_text_query_unknown_session(query_text)
        self.visor_controller.interface.delete_text_query(query_text, engine)
        return HttpResponse()


    @method_decorator(require_GET)
    def exec_query(self, request):
        """
            Callback function for executing query.
            Only GET requests are allowed.
            Arguments:
               request: request object specifying the id of the query to be executed
            Returns:
               HTTP 200 containing a dictionary with the status of the query execution.
        """
        query_id = request.GET.get('qsid', None)
        if query_id == None:
            raise Http404("Query ID not specified. Query does not exist")

        query_data = self.visor_controller.execquery_impl(query_id, request.session.session_key, False)

        # transform system paths to browser-like paths before sending out the response
        for idx in range(len(query_data.status.postrainimg_paths)):
            query_data.status.postrainimg_paths[idx] = query_data.status.postrainimg_paths[idx].replace(os.sep, '/')
        for idx in range(len(query_data.status.curatedtrainimgs_paths)):
            query_data.status.curatedtrainimgs_paths[idx] = query_data.status.curatedtrainimgs_paths[idx].replace(os.sep, '/')

        return HttpResponse(json.dumps(query_data.status.to_dict()))


    @method_decorator(require_GET)
    def get_backend_reachable(self, request):
        """
            Checks whether backend is running and reachable.
            Only GET requests are allowed.
            Arguments:
               request: request object only used to check that it is a GET
            Returns: HTTP Response containing the string representation
                     of a boolean indicating whether the backend services
                     are reachable or not. "0" represents False.
        """
        return HttpResponse(self.visor_controller.is_backend_reachable())


    @method_decorator(require_GET)
    def get_image(self, request, img_set):
        """
            Gets an image from one of the various image sets stored in the site.
            The path to the file relative to the root of the site should be received. The path is completed
            with information extracted for the settings of the site.
            Only GET requests are allowed.
            Arguments:
               request: request object specifying the relative path to the file in the site
            Returns:
               HTTP 200 containing the image data, HTTP 404 is the image is not found
        """
        url_path = request.get_full_path()
        roi_dict = None
        dataset = None

        # if multiple image paths are specified, take just the first one,
        # but be sure to extract the dataset name first, if present
        if ';' in url_path:
            for item in url_path.split(";"):
                if 'dataset:' in item:
                    dataset = item.split(":")[1]
                    break
            url_path = url_path[url_path.find(';')]

        # This could happen when the search is triggered from the training images page
        if 'uploadedimgs/postrainimgs' in url_path:
            url_path = url_path.replace('uploadedimgs/postrainimgs', 'postrainimgs')
            img_set = 'postrainimgs'

        # This could happen when the search is triggered from the training images page
        if 'uploadedimgs/curatedtrainimgs' in url_path:
            url_path = url_path.replace('uploadedimgs/curatedtrainimgs', 'curatedtrainimgs')
            img_set = 'curatedtrainimgs'

        # if present, separate image path from roi/uri info
        if ('roi:' in url_path) or ('uri:' in url_path) or ('dataset:' in url_path) or ('anno:' in url_path):
            extra_param_indexes = [url_path.find('roi:'), url_path.find('uri:'), url_path.find('dataset:'), url_path.find('anno:')]
            extra_param_indexes = filter(lambda a: a != -1, extra_param_indexes)
            extra_param_min = min(extra_param_indexes)
            extra_params = url_path[extra_param_min:]
            url_path = url_path[:extra_param_min-1]
            roi_dict = dict(item.split(":") for item in extra_params.split(",") if 'roi' in item)
            # uri_dict only used for passing information to the backend
            # uri_dict = dict(item.split(":") for item in extra_params.split(",") if 'uri' in item)
            for item in extra_params.split(","):
                if 'dataset:' in item:
                    dataset = item.split(":")[1]
                    break

        # If it is an uploaded image (with a roi or not), it could relate to an image that
        # has been uploaded by the user, or an image that was selected in the search results.
        # If it corresponds to the latter, redirect the search to 'datasets' in
        # an attempt to find the right image.
        # This could happen mostly when showing the thumbnail image in the query bar, in which
        # case it is not useful to show a ROI, so do not draw it !
        if ('uploadedimgs' in url_path) and dataset:
            path_in_datasets = url_path.replace('uploadedimgs', 'datasets/' + dataset)
            full_path_in_datasets = path_in_datasets.replace(settings.SITE_PREFIX + '/datasets', settings.PATHS['datasets'])
            if os.path.exists(full_path_in_datasets):
                url_path = path_in_datasets
                img_set = 'datasets'
                roi_dict = None # In this case do not draw a ROI

        # redirect curated images to their correct folder, if needed
        if 'curated__' in url_path:
            url_path = url_path.replace('postrainimgs', 'curatedtrainimgs')
            img_set = 'curatedtrainimgs'

        real_path = urllib.unquote(url_path).replace(settings.SITE_PREFIX + '/' + img_set, settings.PATHS[img_set])

        if not os.path.exists(real_path):
            raise Http404('Requested image ' + url_path + ' does not exist')

        img = self.visor_controller.get_image(real_path, roi_dict, as_thumbnail=(img_set == 'thumbnails'), just_ROI=(img_set == 'regions'))

        response = HttpResponse(content_type="image/*")
        if not img.format:
            img.save(response, "JPEG")
        else:
            img.save(response, img.format)
        return response


    @method_decorator(require_POST)
    def upload_image(self, request):
        """
            Uploads an image to the site. The request should contain either the image data submitted from a form
            or an url where to download the image from.
            Only POST requests are allowed. This method is CSRF protected.
            Arguments:
               request: request object specifying either image data (not encoded) or an url
            Returns:
               HTTP 200 containing a JSON describing the uploaded image or an error
        """
        jsonstr = ''
        if len(request.FILES) == 0:
            fileurl = request.POST.get('url', None)
            img_data = request.POST.get('img_data', None)
            if fileurl:
                jsonstr = self.visor_controller.uploadimage(None, fileurl, None)
            if img_data:
                img_data_dict = ast.literal_eval(img_data)
                jsonstr = self.visor_controller.uploadimage(None, None, img_data_dict, is_data_base64=True)
        else:
            img = request.FILES['file']
            filename = str(request.FILES['file'])
            data = str(img.read())
            jsonstr = self.visor_controller.uploadimage(None, None, img_data={'filename': filename, 'data': data})

        if jsonstr == '':
            jsonstr = json.dumps({'Error': 'Error uploading image', 'srcurl': fileurl, 'impath': None})

        return HttpResponse(jsonstr)


    @method_decorator(login_required)
    @method_decorator(require_POST)
    def start_backend(self, request):
        """
            API function that starts the backend service.
            Arguments:
               request: request object containing details of the user session, etc.
        """
        if self.backend_thread and not self.backend_thread.is_alive():
            self.backend_thread = None
        engine = ''
        if 'engine_name' in request.POST:
            engine = request.POST['engine_name']
        else:
            message = 'The engine name was not specified in the request. Cannot proceed with the starting procedure.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})
        if not self.backend_thread:
            print 'Starting backend service...'
            self.backend_thread = threading.Thread(target=api_globals.start_backend_service, args=(engine,))
            self.backend_thread.start()
            message = 'Starting the backend service ... This process might take a couple of minutes. Please go back to the Home page and wait for the backend to respond.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})
        elif self.backend_thread.is_alive():
            message = 'A previous attempt to start/stop the backend is not finished yet. Please wait.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})
        else:
            return redirect('admintools')


    @method_decorator(login_required)
    @method_decorator(require_POST)
    def stop_backend(self, request):
        """
            API function that stops the backend service.
            Arguments:
               request: request object containing details of the user session, etc.
        """
        if self.backend_thread and not self.backend_thread.is_alive():
            self.backend_thread = None
        engine = ''
        if 'engine_name' in request.POST:
            engine = request.POST['engine_name']
        else:
            message = 'The engine name was not specified in the request. Cannot proceed with the starting procedure.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})
        if not self.backend_thread:
            print 'Stopping backend service...'
            self.backend_thread = threading.Thread(target=api_globals.stop_backend_service, args=(engine,))
            self.backend_thread.start()
            message = 'Stopping the backend service ... This process might take a few seconds. To check the backend is off-line, please go back to the Home page and refresh the page until you can see a message indicating that there is an error interacting with the backend.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})
        elif self.backend_thread.is_alive():
            message = 'A previous attempt to start/stop the backend is not finished yet. Please wait.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})
        else:
            return redirect('admintools')


    @method_decorator(require_GET)
    def get_keyword_list(self, request):
        """
            Retrieves a list of keywords extracted from the metadata of the defined dataset.
            The list depends on a search 'term' specified in the request.
            Only GET requests are allowed.
            Arguments:
               request: request object specifying the search 'term'
            Returns:
               JSON containing the list of keywords in the form: { 'results':  <list of keywords> }.
               <list of keywords> will be empty on case of errors.
        """
        json_response = {"results": []}
        term_text = ''
        if 'term' in request.GET:
            term_text = request.GET['term']

        try:
            keyword_list = self.visor_controller.metadata_handler.get_search_suggestions(term_text)
            for idx in range(len(keyword_list)):
                json_response["results"].append({'id': idx+1, 'text': keyword_list[idx]})
        except Exception as e:
            print e
            json_response = {"results": []}
            pass

        return HttpResponse(json.dumps(json_response))


    @method_decorator(require_GET)
    def get_text_suggestions(self, request):
        """
            Retrieves a list of words suggested for the autocomplete of the main page.
            Only GET requests are allowed.
            The backend engine specified in the request must support the 'getSearchSuggestions'
            method, or an empty list of results will be returned.
            NOTE: It sends the request to the backend directly, without going through
            the controller/interface/engine.
            Arguments:
               request: request object specifying the query string in the field 'query' and
               the target engine in the 'engine' field.
            Returns:
               JSON containing the suggestions in the form: { 'success': True, results': <list of results> },
               or an empty JSON if there was an error.
        """
        json_response = {}
        if 'query' not in request.GET or 'engine' not in request.GET:
            return HttpResponse(json.dumps(json_response))
        query_text = ''

        try:
            if request.GET['engine'] in self.visor_controller.opts.engines_dict:
                backend_port = self.visor_controller.opts.engines_dict[request.GET['engine']]['backend_port']
                ses = retengine.engine.backend_client.Session(backend_port)
                query_text = request.GET['query']
                func_in = {}
                func_in['func'] = 'getSearchSuggestions'
                func_in['query_string'] = query_text
                request = json.dumps(func_in)
                response = ses.custom_request(request)
                json_response = json.loads(response)
                if not json_response["success"]:
                    json_response = {}
        except:
            json_response = {}
            pass

        # last chance to get a suggestion, use the keywords in the metadata
        if json_response == {}:
            try:
                json_response["results"] = []
                json_response["success"] = True
                keyword_list = self.visor_controller.metadata_handler.get_search_suggestions(query_text)
                if settings.KEYWORDS_WILDCARD in keyword_list:
                    keyword_list.remove(settings.KEYWORDS_WILDCARD)
                for idx in range(len(keyword_list)):
                    json_response["results"].append(keyword_list[idx])
            except:
                json_response = {}
                pass

        return HttpResponse(json.dumps(json_response))


    @method_decorator(login_required)
    @method_decorator(require_GET)
    def pipeline_input_status(self, request):
        """
            Renders the user page that checks/displays the status of the pipeline input checking
            Arguments:
               request: request object containing details of the user session, etc.
        """
        if self.pipeline_input_thread != None:

            if self.pipeline_input_thread.is_alive():
                home_location = settings.SITE_PREFIX + '/'
                if 'HTTP_X_FORWARDED_HOST' in request.META:
                    home_location = 'http://' + request.META['HTTP_X_FORWARDED_HOST'] + home_location
                context = {
                'NUM_FILES_CHECKED': len(self.pipeline_frame_list),
                'TOTAL_NUM_FILES': self.total_input_files,
                'HOME_LOCATION': home_location,
                }
                return render(request, 'pipeline_input_status.html', context)
            else:
                if len(self.pipeline_frame_list) == 0:
                    message = 'No valid input images were found. The pipeline cannot be started.'
                    redirect_to = settings.SITE_PREFIX + '/admintools'
                    return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})
                else:
                    self.pipeline_input_thread = None
                    return redirect('pipeline_start')

        else:

            if len(self.threads_map) != 0:
                for thread_index in self.threads_map:
                    if self.threads_map[thread_index].is_alive():
                        message = 'There is a pipeline running !. Please wait.'
                        redirect_to = settings.SITE_PREFIX + '/pipeline_input_status'
                        return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})
            else:
                message = 'There is no pipeline running !'
                redirect_to = settings.SITE_PREFIX + '/admintools'
                return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})


    @method_decorator(login_required)
    @method_decorator(require_POST)
    def pipeline_input(self, request):
        """
            API function that gathers the input data for the pipeline and then redirects to the pipeline start page.
            Arguments:
               request: request object containing details of the user session, etc.
        """
        if ('input_type' not in request.POST) or (request.POST['input_type'] not in ['positive', 'negative', 'video']):
            message = 'The input type descriptor is missing or invalid. The pipeline cannot be started.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})

        if ('input_type' not in request.POST) or (request.POST['input_type'] not in ['positive', 'negative', 'video']):
            message = 'The input type descriptor is missing or invalid. The pipeline cannot be started.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})

        if ('engine' not in request.POST) or (request.POST['engine'] not in self.ENGINES_WITH_PIPELINE):
            message = 'There is no data pipeline defined for the selected engine. A pipeline cannot be started.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})

        if self.pipeline_input_type != 'video':
            check_one = len(request.FILES.getlist('input_file'))>0 and len(request.FILES.getlist('input_json'))>0
            check_two = len(request.POST.get('input_url', ''))>0  and (len(request.FILES.getlist('input_file'))>0 or len(request.FILES.getlist('input_json'))>0)
            if check_one or check_two:
                message = 'Please choose just one input to the pipeline. The pipeline cannot be started.'
                redirect_to = settings.SITE_PREFIX + '/admintools'
                return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})

        if request.POST['engine'] == 'faces' and request.POST['input_type'] == 'video':
            file_list = request.FILES.getlist('input_video_list')
            if len(file_list) == 0:
                message = 'The input file for video ingestion is missing. A pipeline cannot be started.'
                redirect_to = settings.SITE_PREFIX + '/admintools'
                return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})
            elif not file_list[0].name.endswith('.txt'):
                message = 'The input file for video ingestion does not appear to be a text file. A pipeline cannot be started.'
                redirect_to = settings.SITE_PREFIX + '/admintools'
                return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})

        # get engine config
        (self.DATASET_IM_BASE_PATH, self.DATASET_IM_PATHS,
        self.NEGATIVE_IM_PATHS, self.NEGATIVE_IM_BASE_PATH,
        self.DATASET_FEATS_FILE, self.NEG_FEATS_FILE) = self.get_engine_config(request.POST['engine'])

        self.pipeline_input_type = request.POST['input_type']
        img_base_path = self.DATASET_IM_BASE_PATH
        file_with_list_of_paths = self.DATASET_IM_PATHS
        if self.pipeline_input_type == 'negative':
            img_base_path = self.NEGATIVE_IM_BASE_PATH
            file_with_list_of_paths = self.NEGATIVE_IM_PATHS

        if not img_base_path or not file_with_list_of_paths:
            message = 'The image source paths for the current engine are not properly set. The pipeline cannot be started.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})

        if len(self.threads_map) != 0 or self.pipeline_input_thread != None:
            for thread_index in self.threads_map:
                if self.threads_map[thread_index].is_alive():
                    message = 'There is a pipeline running !. Please wait.'
                    redirect_to = settings.SITE_PREFIX + '/pipeline_status'
                    return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})

        self.threads_map.clear()
        self.pipeline_frame_list = []
        self.pipeline_video_list = []
        self.global_input_index = -1
        self.pipeline_engine = request.POST['engine']
        self.total_input_files = None

        file_system_encoding_not_UTF8 = sys.getfilesystemencoding().lower() != 'utf-8'
        if file_system_encoding_not_UTF8:
            img_base_path = str(img_base_path)  # convert to the system's 'str' to avoid problems with the 'os' module in non-utf-8 systems

        if self.pipeline_input_type != 'video' and len(request.FILES) == 0:
            url = request.POST.get('input_url', None)
            if url is None or len(url)==0:
                # if no input file or list is provided with the names of the files to ingest, ingest the whole directory by default
                self.pipeline_input_thread = threading.Thread(target=api_globals.gather_pipeline_input,
                                args=('dir', img_base_path, None, file_system_encoding_not_UTF8, self.pipeline_frame_list), )
                # start the thread and redirect to the status-checking page
                self.pipeline_input_thread.start()
                return redirect('pipeline_input_status')
            else:
                # get the list of files from a IIIF manifest that is online, pointed at by the specified URL
                dset = settings.VISOR['datasets'].keys()[0] # I don't like this, but we have to do it like this for now
                metadata_dir = os.path.join(self.visor_controller.metadata_paths.metadata , dset)
                self.pipeline_input_thread = threading.Thread(target=api_globals.gather_pipeline_input,
                                args=('url', img_base_path, [url], file_system_encoding_not_UTF8, self.pipeline_frame_list, metadata_dir), )
                # start the thread and redirect to the status-checking page
                self.pipeline_input_thread.start()
                return redirect('pipeline_input_status')

        if len(request.FILES) != 0:

            if self.pipeline_input_type == 'video':
                # for videos, just go straight to the pipeline
                file_list = request.FILES.getlist('input_video_list')
                uploaded_file = file_list[0].read()
                file_list = uploaded_file.split('\n')
                if len(file_list[-1]) == 0:
                    file_list = file_list[:-1]
                self.total_input_files = len(file_list)
                self.pipeline_video_list = file_list
                return redirect('pipeline_start')

            file_list = request.FILES.getlist('input_file')
            if len(file_list)>0:
                if len(file_list) == 1 and file_list[0].name.endswith('.txt'):
                    # This allows the possibility of uploading a list of images in a text file
                    # However, the whole file must be read before leaving this thread and starting the other.
                    uploaded_file = file_list[0].read()
                    file_list = uploaded_file.split('\n')
                    if len(file_list[-1]) == 0:
                        file_list = file_list[:-1]
                    self.total_input_files = len(file_list)

                    # check the number of images to ingest. If less than MIN_NUMBER_INPUT_THREAD_INDIVIDUAL_FILES don't start a separate thread
                    if self.total_input_files < settings.MIN_NUMBER_INPUT_THREAD_INDIVIDUAL_FILES:
                        api_globals.gather_pipeline_input('file', img_base_path, file_list, file_system_encoding_not_UTF8, self.pipeline_frame_list)
                        return redirect('pipeline_start')
                    else:
                        self.pipeline_input_thread = threading.Thread(target=api_globals.gather_pipeline_input,
                                args=('file', img_base_path, file_list, file_system_encoding_not_UTF8, self.pipeline_frame_list))
                        # start the thread and redirect to the status-checking page
                        self.pipeline_input_thread.start()
                        return redirect('pipeline_input_status')
            elif len(request.FILES.getlist('input_json')) == 1 :
                # get the list of files from a local IIIF manifest in JSON format
                json_file_in = request.FILES.getlist('input_json')[0]
                temp_json_file = tempfile.NamedTemporaryFile(delete=False)
                for chunk in json_file_in.chunks():
                    temp_json_file.write(chunk)
                temp_json_file.close()
                dset = settings.VISOR['datasets'].keys()[0] # I don't like this, but we have to do it like this for now
                metadata_dir = os.path.join(self.visor_controller.metadata_paths.metadata , dset)
                self.pipeline_input_thread = threading.Thread(target=api_globals.gather_pipeline_input,
                                args=('json', img_base_path, [temp_json_file.name], file_system_encoding_not_UTF8,
                                    self.pipeline_frame_list, metadata_dir), )
                # start the thread and redirect to the status-checking page
                self.pipeline_input_thread.start()
                return redirect('pipeline_input_status')
            else:
                # When uploading files in this way, we cannot use a separate thread, since the files are loaded in memory as stream
                # objects by Django and if we start another thread the streams are closed, so the separate thread cannot save them.
                # Therefore, the files must be checked and saved in this thread. Apply all limitations here and in the corresponding HTML.
                if len(file_list) > settings.MAX_NUMBER_UPLOAD_INDIVIDUAL_FILES:
                    # abort !. File ingestion might take too long a lead to a time-out or a crash
                    message = ('You can only upload a maximum of %d files in total. Please select less files and try again. ') % settings.MAX_NUMBER_UPLOAD_INDIVIDUAL_FILES
                    redirect_to = settings.SITE_PREFIX + '/admintools'
                    return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})
                total_size = 0
                for afile in file_list:
                    filename, file_extension = os.path.splitext(afile.name)
                    total_size = total_size + afile.size
                    # check the accumulated total size of the files to be ingested
                    if total_size > settings.MAX_TOTAL_SIZE_UPLOAD_INDIVIDUAL_FILES:
                        # abort !. File ingestion might take too long a lead to a time-out or a crash
                        message = ('You can only upload a maximum of %d MB in total. Please select less files and try again. ') % (settings.MAX_TOTAL_SIZE_UPLOAD_INDIVIDUAL_FILES/1048576)
                        redirect_to = settings.SITE_PREFIX + '/admintools'
                        return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})
                    # check all files for a valid image extension
                    if file_extension.lower() not in settings.VALID_IMG_EXTENSIONS:
                        # otherwise, abort !. This might seem drastic, but it is better to
                        # keep the image folder clean !.
                        message = ('Input file %s does not seem to be an image, as it does not have any of the following extensions: %s. Please remove this file and try again. ') % (afile.name, str(settings.VALID_IMG_EXTENSIONS_STR))
                        redirect_to = settings.SITE_PREFIX + '/admintools'
                        return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})
                # ... and if we made it until here, try to upload all selected files and copy them to the images folder
                for afile in file_list:
                    full_path = os.path.join(img_base_path, afile.name)
                    # save the file to disk
                    if file_system_encoding_not_UTF8:
                        full_path = full_path.encode('utf-8') # if needed, convert from utf-8
                    with open(full_path, 'wb+') as destination:
                        for chunk in afile.chunks():
                            destination.write(chunk)
                    self.pipeline_frame_list.append(afile.name)
                # ... and if we made it until here, we are ready to start the pipeline
                return redirect('pipeline_start')

        message = 'The input to the pipeline is invalid!. Please try again.'
        redirect_to = settings.SITE_PREFIX + '/admintools'
        return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})


    @method_decorator(login_required)
    @method_decorator(require_GET)
    def pipeline_start(self, request):
        """
            API function that start the execution of the pipeline and then redirects to the status page.
            Arguments:
               request: request object containing details of the user session, etc.
        """
        if len(self.threads_map) != 0 or self.pipeline_input_thread != None:
            for thread_index in self.threads_map:
                if self.threads_map[thread_index].is_alive():
                    message = 'There is a pipeline running !. Please wait.'
                    redirect_to = settings.SITE_PREFIX + '/pipeline_status'
                    return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})

        if len(self.pipeline_frame_list) == 0 and self.pipeline_input_type != 'video':
            self.total_input_files = None
            message = 'No valid input images were found. The pipeline cannot be started.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})

        if len(self.pipeline_video_list) == 0 and self.pipeline_input_type == 'video':
            self.total_input_files = None
            message = 'No video paths were provided. The pipeline cannot be started.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})


        # get engine config
        (self.DATASET_IM_BASE_PATH, self.DATASET_IM_PATHS,
        self.NEGATIVE_IM_PATHS, self.NEGATIVE_IM_BASE_PATH,
        self.DATASET_FEATS_FILE, self.NEG_FEATS_FILE) = self.get_engine_config(self.pipeline_engine)

        img_base_path = self.DATASET_IM_BASE_PATH
        file_with_list_of_paths = self.DATASET_IM_PATHS
        dataset_features_out_file = self.DATASET_FEATS_FILE
        if self.pipeline_input_type == 'negative':
            img_base_path = self.NEGATIVE_IM_BASE_PATH
            file_with_list_of_paths = self.NEGATIVE_IM_PATHS
            dataset_features_out_file = self.NEG_FEATS_FILE

        if not img_base_path or not file_with_list_of_paths:
            message = 'The image source paths for the current engine are not properly set. The pipeline cannot be started.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})

        # finally ready to start ..
        if self.pipeline_engine == 'cpuvisor-srv':

            # Calculate number of threads. Set to a maximum of settings.FRAMES_THREAD_NUM_LIMIT and a minimum of 1.
            num_threads = max(1, min(len(self.pipeline_frame_list)/settings.PREPROC_CHUNK_SIZE, settings.FRAMES_THREAD_NUM_LIMIT))

            # if the 'negative' features are being computed, always use one thread,
            # as 'cpuvisor_preproc' does not support chunks for negative features
            chunk_size = settings.PREPROC_CHUNK_SIZE
            if self.pipeline_input_type == 'negative':
                num_threads = 1
                chunk_size = len(self.pipeline_frame_list) + 1

            # Start pipeline.
            self.global_input_index = 0
            for i in range(0, num_threads):
                list_end = min(self.global_input_index + chunk_size, len(self.pipeline_frame_list))
                frame_list = self.pipeline_frame_list[self.global_input_index : list_end]
                chunk_thread = threading.Thread(target=data_processing_pipeline_cpuvisor,
                               args=(frame_list, self.global_input_index, self.lock, self.pipeline_input_type,
                                     img_base_path, file_with_list_of_paths,
                                     settings.CONFIG_PROTO_PATH, chunk_size))
                chunk_thread.start()
                self.threads_map[self.global_input_index] = chunk_thread
                self.global_input_index = list_end

        if self.pipeline_engine == 'faces' and self.pipeline_input_type != 'video':

            # Calculate number of threads. Set to a maximum of settings.FRAMES_THREAD_NUM_LIMIT and a minimum of 1.
            num_threads = max(1, min(len(self.pipeline_frame_list)/settings.PREPROC_CHUNK_SIZE, settings.FRAMES_THREAD_NUM_LIMIT))

            # Start pipeline.
            self.global_input_index = 0
            for i in range(0, num_threads):
                list_end = min(self.global_input_index + settings.PREPROC_CHUNK_SIZE, len(self.pipeline_frame_list))
                frame_list = self.pipeline_frame_list[self.global_input_index : list_end]
                chunk_thread = threading.Thread(target=data_processing_pipeline_faces,
                               args=(frame_list, 'images', # face engine always ingest images if self.pipeline_input_type != 'video'
                                     self.global_input_index, self.lock,
                                     img_base_path, file_with_list_of_paths,
                                     dataset_features_out_file))
                chunk_thread.start()
                self.threads_map[self.global_input_index] = chunk_thread
                self.global_input_index = list_end

        if self.pipeline_engine == 'faces' and self.pipeline_input_type == 'video':

            # Calculate number of threads. Set to a maximum of self.num_video_threads.
            num_threads = min(len(self.pipeline_video_list), self.num_video_threads)

            self.global_input_index = 0
            for i in range(0, num_threads):
                list_end = min(self.global_input_index + self.video_chunk_size, len(self.pipeline_video_list))
                video_list = self.pipeline_video_list[self.global_input_index : list_end]
                chunk_thread = threading.Thread(target=data_processing_pipeline_faces,
                               args=(video_list,
                                     self.pipeline_input_type,
                                     self.global_input_index, self.lock,
                                     img_base_path, file_with_list_of_paths,
                                     dataset_features_out_file))
                chunk_thread.start()
                self.threads_map[self.global_input_index] = chunk_thread
                self.global_input_index = list_end

        return redirect('pipeline_status')


    @method_decorator(login_required)
    @method_decorator(require_GET)
    def pipeline_status(self, request):
        """
            Renders the user page that checks/displays the status of the pipeline execution
            Arguments:
               request: request object containing details of the user session, etc.
        """
        if len(self.threads_map) == 0:
            message = 'There is NO data pipeline running !.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})

        alive_thread_counter = 0
        done_thread_counter = 0
        for thread_index in self.threads_map:
            if self.threads_map[thread_index].is_alive():
                alive_thread_counter = alive_thread_counter + 1
            else:
                done_thread_counter = done_thread_counter + 1

        number_of_videos = len(self.pipeline_video_list)
        number_of_frames = len(self.pipeline_frame_list)
        processing_frames = number_of_frames > 0
        processing_video = number_of_videos > 0
        number_of_frame_chunks = 0

        if self.pipeline_engine == 'faces' and self.pipeline_input_type != 'video':

            number_of_frame_chunks = int(round((number_of_frames /settings.PREPROC_CHUNK_SIZE*1.0) + 0.5))

            if alive_thread_counter == 0 and processing_frames and self.global_input_index + 1 > number_of_frames:
                message = 'The data pipeline has finished !.'
                redirect_to = settings.SITE_PREFIX + '/admintools'
                return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})
            elif processing_frames and alive_thread_counter < settings.FRAMES_THREAD_NUM_LIMIT and self.global_input_index + 1 <= number_of_frames:
                # since we are under the FRAMES_THREAD_NUM_LIMIT quota, let's try to start a new thread for the next chunk of frames

                img_base_path = self.DATASET_IM_BASE_PATH
                file_with_list_of_paths = self.DATASET_IM_PATHS
                dataset_features_out_file = self.DATASET_FEATS_FILE
                list_end = min(self.global_input_index + settings.PREPROC_CHUNK_SIZE, number_of_frames)
                frame_list = self.pipeline_frame_list[self.global_input_index : list_end]
                if len(frame_list) > 0:
                    chunk_thread = threading.Thread(target=data_processing_pipeline_faces,
                                   args=(frame_list, 'images', # face engine always ingest images if self.pipeline_input_type != 'video'
                                         self.global_input_index, self.lock,
                                         img_base_path, file_with_list_of_paths,
                                         dataset_features_out_file))
                    chunk_thread.start()
                    self.threads_map[self.global_input_index] = chunk_thread
                    self.global_input_index = list_end

        if self.pipeline_engine == 'faces' and self.pipeline_input_type == 'video':

            if alive_thread_counter == 0 and processing_video and self.global_input_index + 1 > number_of_videos:
                message = 'The data pipeline has finished !.'
                redirect_to = settings.SITE_PREFIX + '/admintools'
                return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})
            elif processing_video and alive_thread_counter < self.num_video_threads and self.global_input_index + 1 <= number_of_videos:
                # since we are under the self.num_video_threads quota, let's try to start a new thread for the next video

                img_base_path = self.DATASET_IM_BASE_PATH
                file_with_list_of_paths = self.DATASET_IM_PATHS
                dataset_features_out_file = self.DATASET_FEATS_FILE
                list_end = min(self.global_input_index + self.video_chunk_size, number_of_videos)
                video_list = self.pipeline_video_list[self.global_input_index : list_end]
                if len(video_list) > 0:
                    chunk_thread = threading.Thread(target=data_processing_pipeline_faces,
                                   args=(video_list, self.pipeline_input_type,
                                         self.global_input_index, self.lock,
                                         img_base_path, file_with_list_of_paths,
                                         dataset_features_out_file))
                    chunk_thread.start()
                    self.threads_map[self.global_input_index] = chunk_thread
                    self.global_input_index = list_end

        if self.pipeline_engine == 'cpuvisor-srv':

            number_of_frame_chunks = int(round((number_of_frames /settings.PREPROC_CHUNK_SIZE*1.0) + 0.5))

            # if the 'negative' features are being computed, we always use one thread,
            # as 'cpuvisor_preproc' does not support chunks for negative features
            if self.pipeline_input_type == 'negative':
                number_of_frame_chunks = 1 # so there is always one one chunk

            if alive_thread_counter == 0 and processing_frames and self.global_input_index + 1 >= number_of_frames:
                message = 'The data pipeline has finished !.'
                redirect_to = settings.SITE_PREFIX + '/admintools'
                return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})
            elif processing_frames and alive_thread_counter < settings.FRAMES_THREAD_NUM_LIMIT and self.global_input_index + 1 < number_of_frames:
                # since we are under the FRAMES_THREAD_NUM_LIMIT quota, let's try to start a new thread for the next chunk of frames

                img_base_path = self.DATASET_IM_BASE_PATH
                file_with_list_of_paths = self.DATASET_IM_PATHS
                if self.pipeline_input_type == 'negative':
                    img_base_path = self.NEGATIVE_IM_BASE_PATH
                    file_with_list_of_paths = self.NEGATIVE_IM_PATHS

                list_end = min(self.global_input_index + settings.PREPROC_CHUNK_SIZE, number_of_frames)
                frame_list = self.pipeline_frame_list[self.global_input_index : list_end]
                if len(frame_list) > 0:
                    chunk_thread = threading.Thread(target=data_processing_pipeline_cpuvisor,
                                   args=(frame_list, self.global_input_index, self.lock, self.pipeline_input_type,
                                         img_base_path, file_with_list_of_paths,
                                         settings.CONFIG_PROTO_PATH, settings.PREPROC_CHUNK_SIZE))
                    chunk_thread.start()
                    self.threads_map[self.global_input_index] = chunk_thread
                    self.global_input_index = list_end


        home_location = settings.SITE_PREFIX + '/'
        if 'HTTP_X_FORWARDED_HOST' in request.META:
            home_location = 'http://' + request.META['HTTP_X_FORWARDED_HOST'] + home_location

        context = {
        'PROCESSED_VIDEOS': done_thread_counter,
        'PROCESSED_FRAME_CHUNKS': done_thread_counter,
        'TOTAL_VIDEOS': number_of_videos,
        'TOTAL_FRAME_CHUNKS': number_of_frame_chunks,
        'TOTAL_FRAMES': number_of_frames,
        'HOME_LOCATION': home_location,
        }
        return render(request, 'pipeline_status.html', context)


    @method_decorator(login_required)
    @method_decorator(require_POST)
    def clear_backend(self, request):
        """
            API function that clears the data files used by the backend service.
            Arguments:
               request: request object containing details of the user session, etc.
        """
        if ('input_type' not in request.POST) or (request.POST['input_type'] not in ['positive', 'negative']):
            message = 'The input type descriptor is missing or invalid. The clearing cannot be started.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})

        if ('engine' not in request.POST) or (request.POST['engine'] not in self.ENGINES_WITH_PIPELINE):
            message = 'There is no data pipeline defined for the selected engine. A pipeline cannot be started.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})

        # get engine config
        (self.DATASET_IM_BASE_PATH, self.DATASET_IM_PATHS,
        self.NEGATIVE_IM_PATHS, self.NEGATIVE_IM_BASE_PATH,
        self.DATASET_FEATS_FILE, self.NEG_FEATS_FILE) = self.get_engine_config(request.POST['engine'])

        clear_backend_type = request.POST['input_type']
        feats_file = self.DATASET_FEATS_FILE
        file_with_list_of_paths = self.DATASET_IM_PATHS
        if clear_backend_type == 'negative':
            feats_file = self.NEG_FEATS_FILE
            file_with_list_of_paths = self.NEGATIVE_IM_PATHS

        if not feats_file:
            message = 'The positive/negative feature files of the engine are not properly set. The clearing cannot be started.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})

        try:
            if clear_backend_type == 'negative':
                # there is only one negative features file
                os.remove(feats_file)
            else:
                # there can be several positive features files, so search
                # for them and remove them all
                path, filename = os.path.split(feats_file)
                filename = filename.replace('.', '*.')
                for afile in glob.glob(os.path.join(path, filename)):
                    os.remove(afile)
            if os.path.exists(file_with_list_of_paths):
                os.remove(file_with_list_of_paths)
        except Exception as e:
            message = 'There was an error while clearing the backend. Exception: ' + str(e)
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})

        message = 'The ' + clear_backend_type + ' backend data has been cleared!.'
        redirect_to = settings.SITE_PREFIX + '/admintools'
        return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})


    @method_decorator(login_required)
    @method_decorator(require_POST)
    def metadata_reset(self, request):
        """
            API function that clears the metadata index used by the frontend.
            Arguments:
               request: request object containing details of the user session, etc.
        """
        if self.visor_controller.reset_metadata_index():
            message = 'The metadata index has been cleared and it will start rebuilding. This process might take a few minutes. In the meantime the metadata information will be partially available.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})
        else:
            message = 'Either there is no metadata available or the metadata index is still loading information (please wait until it is finished to reset it).'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context={'REDIRECT_TO': redirect_to, 'MESSAGE': message})
