from django.conf import settings
from django.http import HttpResponse, FileResponse, HttpResponseBadRequest, Http404
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render_to_response, render
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

import urllib
import os
import sys
import json
import glob
import fnmatch
import imghdr
from subprocess import Popen, PIPE
import threading
from google.protobuf import text_format

PATH_TO_CAFFE_BACKEND_PROTO = os.path.join(settings.BASE_DIR, '../vgg_classifier/proto')
if os.path.exists(PATH_TO_CAFFE_BACKEND_PROTO):
    sys.path.append(PATH_TO_CAFFE_BACKEND_PROTO) # add this to be able to load cpuvisor_config_pb2
    import cpuvisor_config_pb2

sys.path.append(os.path.join(os.path.dirname(__file__), '../../pipeline')) # add this to be able to load object_pipeline_single_thread
from data_pipeline import data_processing_pipeline

import retengine.engine.backend_client

def start_backend_service(engine):
    """ Body of the thread that runs the script to start the backend service """
    pOpenCmd = [ os.path.join( settings.MANAGE_SERVICE_SCRIPTS_BASE_PATH, 'start_backend_service.sh'), engine ]
    p = Popen(pOpenCmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    p.poll()


def stop_backend_service(engine):
    """ Body of the thread that runs the script to stop the backend service """
    pOpenCmd = [ os.path.join( settings.MANAGE_SERVICE_SCRIPTS_BASE_PATH, 'stop_backend_service.sh'), engine ]
    p = Popen(pOpenCmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    p.poll()


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
        self.visor_controller =  visor_controller
        available_engines =  self.visor_controller.opts.engines_dict
        self.cpuvisor_srv_enabled = False

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
        self.global_input_index = -1
        self.pipeline_input_type = ''

        # init vars to support backen service management
        self.backend_thread = None

        if 'cpuvisor-srv' in available_engines.keys():
            self.cpuvisor_srv_enabled = True
            # read cpuvisor configuration file
            cpuvisorConfigProto = cpuvisor_config_pb2.Config()
            cpuvisorConfigFile = open(settings.CONFIG_PROTO_PATH, "r")
            text_format.Merge(str(cpuvisorConfigFile.read()), cpuvisorConfigProto)
            cpuvisorConfigFile.close()

            # Get some info from the proto config
            self.DATASET_IM_BASE_PATH = cpuvisorConfigProto.preproc_config.dataset_im_base_path
            self.DATASET_IM_PATHS = cpuvisorConfigProto.preproc_config.dataset_im_paths
            self.NEGATIVE_IM_PATHS = cpuvisorConfigProto.preproc_config.neg_im_paths
            self.NEGATIVE_IM_BASE_PATH = cpuvisorConfigProto.preproc_config.neg_im_base_path
            self.DATASET_FEATS_FILE =  cpuvisorConfigProto.preproc_config.dataset_feats_file
            self.NEG_FEATS_FILE = cpuvisorConfigProto.preproc_config.neg_feats_file


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

        if query_id==None:
           return HttpResponseBadRequest("Query ID not specified")

        if name==None:
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
        if query_text==None or engine==None:
           return HttpResponseBadRequest("Query text not correctly specified or query does not exist")

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
        if query_id==None:
           raise Http404("Query ID not specified. Query does not exist")

        query_data = self.visor_controller.execquery_impl(query_id, request.session.session_key, False)

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
        return HttpResponse( self.visor_controller.is_backend_reachable() )


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
            url_path = url_path[ url_path.find(';') ]

        # This could happend when the search is triggered from the training images page
        if ('uploadedimgs/postrainimgs' in url_path):
            url_path = url_path.replace( 'uploadedimgs/postrainimgs', 'postrainimgs' )
            img_set = 'postrainimgs'

        # This could happend when the search is triggered from the training images page
        if ('uploadedimgs/curatedtrainimgs' in url_path):
            url_path = url_path.replace( 'uploadedimgs/curatedtrainimgs', 'curatedtrainimgs' )
            img_set = 'curatedtrainimgs'

        # if present, separate image path from roi/uri info
        if ('roi:' in url_path) or ('uri:' in url_path) or ('dataset:' in url_path):
            extra_params = url_path[ url_path.find(',')+1:]
            url_path = url_path[ :url_path.find(',')]
            roi_dict = dict( item.split(":") for item in extra_params.split(",") if 'roi' in item)
            # uri_dict only used for passing information to the backend
            # uri_dict = dict( item.split(":") for item in extra_params.split(",") if 'uri' in item)
            for item in extra_params.split(","):
                if 'dataset:' in item:
                    dataset = item.split(":")[1]
                    break

        # If it is an uploaded image (with a roi or not), it could relate to a image that
        # has been uploaded by the user, or an image that was selected in the search results.
        # If it corresponds to the latter, redirect the search to 'datasets' in
        # an attempt to find the rigth image
        if ('uploadedimgs' in url_path) and dataset:
            path_in_datasets = url_path.replace( 'uploadedimgs', 'datasets/' + dataset )
            full_path_in_datasets = path_in_datasets.replace(settings.SITE_PREFIX + '/datasets' , settings.PATHS['datasets'])
            if os.path.exists(full_path_in_datasets):
                url_path = path_in_datasets
                img_set = 'datasets'

        # redirect curated images to their correct folder, if needed
        if 'curated__' in url_path:
            url_path = url_path.replace('postrainimgs' , 'curatedtrainimgs')
            img_set = 'curatedtrainimgs'

        real_path = urllib.unquote(url_path).replace(settings.SITE_PREFIX + '/' + img_set , settings.PATHS[img_set])

        if not(os.path.exists(real_path)):
            raise Http404('Requested image ' + url_path + ' does not exist')

        img = self.visor_controller.get_image(real_path, roi_dict, as_thumbnail=(img_set=='thumbnails'))
        response = HttpResponse(content_type="image/*")
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
                jsonstr = self.visor_controller.uploadimage( None , fileurl, None )
            if img_data:
                img_data_dict = ast.literal_eval(img_data)
                jsonstr = self.visor_controller.uploadimage( None , None, img_data_dict, is_data_base64=True )
        else:
            img = request.FILES['file']
            filename = str(request.FILES['file'])
            data = str(img.read())
            jsonstr =  self.visor_controller.uploadimage( None , None, img_data={ 'filename' : filename , 'data': data }  )

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
            return render_to_response("alert_and_redirect.html", context = {'REDIRECT_TO': redirect_to, 'MESSAGE': message } )
        if not self.backend_thread:
            print 'Starting backend service...'
            self.backend_thread = threading.Thread(target=start_backend_service, args=( engine,) )
            self.backend_thread.start()
            message = 'Starting backend service. This process migth take a couple of minutes.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context = {'REDIRECT_TO': redirect_to, 'MESSAGE': message } )
        elif self.backend_thread.is_alive():
            message = 'A previous attempt to start/stop the backend is not finished yet. Please wait.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context = {'REDIRECT_TO': redirect_to, 'MESSAGE': message } )
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
            return render_to_response("alert_and_redirect.html", context = {'REDIRECT_TO': redirect_to, 'MESSAGE': message } )
        if not self.backend_thread:
            print 'Stopping backend service...'
            self.backend_thread = threading.Thread(target=stop_backend_service, args=( engine,) )
            self.backend_thread.start()
            message = 'Stopping backend service. This process migth take a few seconds.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context = {'REDIRECT_TO': redirect_to, 'MESSAGE': message } )
        elif self.backend_thread.is_alive():
            message = 'A previous attempt to start/stop the backend is not finished yet. Please wait.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context = {'REDIRECT_TO': redirect_to, 'MESSAGE': message } )
        else:
            return redirect('admintools')


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
        json_response = []
        if 'query' not in request.GET or 'engine' not in request.GET:
            return HttpResponse(json.dumps(json_response))

        try:
            if request.GET['engine'] in self.visor_controller.opts.engines_dict:
                backend_port = self.visor_controller.opts.engines_dict[ request.GET['engine'] ]['backend_port']
                ses = retengine.engine.backend_client.Session( backend_port)
                func_in = {}
                func_in['func'] = 'getSearchSuggestions'
                func_in['query_string'] = request.GET['query']
                request = json.dumps(func_in)
                response = ses.custom_request(request)
                json_response = json.loads(response)
                if not json_response["success"]:
                    json_response = []
        except:
            json_response = []
            pass

        return HttpResponse(json.dumps(json_response))


    @method_decorator(login_required)
    @method_decorator(require_POST)
    def pipeline_start(self, request):
        """
            API function that start the execution of the pipeline and then redirects to the status page.
            Arguments:
               request: request object containing details of the user session, etc.
        """

        if ('input_type' not in request.POST) or (request.POST['input_type'] not in ['positive', 'negative']):
            message = 'The input type descriptor is missing or invalid. The pipeline cannot be started.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context = {'REDIRECT_TO': redirect_to, 'MESSAGE': message } )

        self.pipeline_input_type = request.POST['input_type']
        img_base_path = self.DATASET_IM_BASE_PATH
        file_with_list_of_paths =  self.DATASET_IM_PATHS
        if self.pipeline_input_type == 'negative':
            img_base_path = self.NEGATIVE_IM_BASE_PATH
            file_with_list_of_paths =  self.NEGATIVE_IM_PATHS

        if not img_base_path or not file_with_list_of_paths:
            message = 'The image source paths for the current engine are not properly set. The pipeline cannot be started.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context = {'REDIRECT_TO': redirect_to, 'MESSAGE': message } )

        if not self.cpuvisor_srv_enabled:
            message = 'Only the caffe engine pipeline is currently supported. The pipeline cannot be started.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context = {'REDIRECT_TO': redirect_to, 'MESSAGE': message } )

        if len(self.threads_map) != 0:
            for thread_index in self.threads_map:
                if self.threads_map[thread_index].is_alive():
                    message = 'There is a pipeline running !. Please wait.'
                    redirect_to = settings.SITE_PREFIX + '/pipeline_status'
                    return render_to_response("alert_and_redirect.html", context = {'REDIRECT_TO': redirect_to, 'MESSAGE': message } )

        self.threads_map.clear()
        self.pipeline_frame_list = []
        self.global_input_index = -1

        if len(request.FILES) == 0:
            # if no input file or list is provided with the names of the files to ingest, so ingest the whole directory by default
            for root, dirnames, filenames in os.walk(img_base_path):
                for filename in fnmatch.filter(filenames, '*'):
                    full_path = os.path.join(root, filename)
                    if os.path.isfile(full_path):
                        relative_path = os.path.join( root.replace(img_base_path,'') , filename)
                        if relative_path.startswith("/"):
                            relative_path = relative_path[1:]
                        # check file is an image...
                        if imghdr.what(full_path) != None:
                            # if it is, add it to the list
                            self.pipeline_frame_list.append(relative_path)
                        # ...skip it otherwise

        if len(request.FILES) != 0:
            file_list = request.FILES.getlist('input_file')
            if len(file_list)==1 and file_list[0].name.endswith('.txt'):
                # let's leave open the possibility of uploading a list of images in a text file
                for frame_path in file_list[0]:
                    frame_path = frame_path.strip()
                    if frame_path.startswith('/'):
                        frame_path = frame_path[1:]
                    full_frame_path = os.path.join( img_base_path, frame_path )
                    # Check frames exists
                    if not os.path.exists(full_frame_path):
                         # abort the process in this case
                        message = ('Input file %s does not exist or cannot be read') % full_frame_path
                        redirect_to = settings.SITE_PREFIX + '/admintools'
                        return render_to_response("alert_and_redirect.html", context = {'REDIRECT_TO': redirect_to, 'MESSAGE': message } )
                    # Check file is an image ..
                    elif imghdr.what(full_frame_path) != None:
                        # if it is, add it to the list
                        self.pipeline_frame_list.append(frame_path)
                    # ...skip it otherwise
            else:
                # otherwise try to upload all selected files and copy them to the images folder
                for afile in file_list:
                    full_path = os.path.join( img_base_path, afile.name )
                    # save the file to disk
                    with open(full_path , 'wb+') as destination:
                        for chunk in afile.chunks():
                            destination.write(chunk)
                    # check file is an image...
                    if imghdr.what(full_path)  != None:
                        # if it is, add it to the list
                        self.pipeline_frame_list.append(afile.name)
                    else:
                        # ...skip it otherwise, and also remove it from the images folder
                        os.remove(full_path)


        # Calculate number of threads. Set to a maximum of settings.FRAMES_THREAD_NUM_LIMIT and a minimum of 1.
        num_threads = max(1, min( len(self.pipeline_frame_list)/settings.PREPROC_CHUNK_SIZE, settings.FRAMES_THREAD_NUM_LIMIT ) )

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
            frame_list = self.pipeline_frame_list[ self.global_input_index : list_end]
            t = threading.Thread( target=data_processing_pipeline,
                        args=(  frame_list, self.global_input_index, self.lock, self.pipeline_input_type,
                                img_base_path, file_with_list_of_paths,
                                settings.CONFIG_PROTO_PATH, chunk_size) )
            t.start()
            self.threads_map[ self.global_input_index ] = t
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
            return render_to_response("alert_and_redirect.html", context = {'REDIRECT_TO': redirect_to, 'MESSAGE': message } )

        aliveThreadCounter = 0
        doneThreadCounter = 0
        for thread_index in self.threads_map:
            if self.threads_map[thread_index].is_alive():
                aliveThreadCounter = aliveThreadCounter + 1
            else:
                doneThreadCounter = doneThreadCounter + 1

        numberOfFrames = len(self.pipeline_frame_list)
        processingFrames = numberOfFrames>0
        numberOfFrameChunks = int ( round( ( numberOfFrames /settings.PREPROC_CHUNK_SIZE*1.0 ) + 0.5 ) )

        # if the 'negative' features are being computed, we always use one thread,
        # as 'cpuvisor_preproc' does not support chunks for negative features
        if self.pipeline_input_type == 'negative':
            numberOfFrameChunks = 1 # so there is always one one chunk

        if aliveThreadCounter == 0 and processingFrames and self.global_input_index + 1 >= numberOfFrames:
            message = 'The data pipeline has finished !.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context = {'REDIRECT_TO': redirect_to, 'MESSAGE': message } )
        elif processingFrames and aliveThreadCounter < settings.FRAMES_THREAD_NUM_LIMIT and self.global_input_index + 1 < numberOfFrames:
            # since we are under the FRAMES_THREAD_NUM_LIMIT quota, let's try to start a new thread for the next chunk of frames

            img_base_path = self.DATASET_IM_BASE_PATH
            file_with_list_of_paths =  self.DATASET_IM_PATHS
            if self.pipeline_input_type == 'negative':
                img_base_path = self.NEGATIVE_IM_BASE_PATH
                file_with_list_of_paths =  self.NEGATIVE_IM_PATHS

            list_end = min(self.global_input_index + settings.PREPROC_CHUNK_SIZE, numberOfFrames)
            frame_list = self.pipeline_frame_list[ self.global_input_index : list_end ]
            if len(frame_list)>0:
                t = threading.Thread( target=data_processing_pipeline,
                        args=(  frame_list, self.global_input_index, self.lock, self.pipeline_input_type,
                                img_base_path, file_with_list_of_paths,
                                settings.CONFIG_PROTO_PATH, settings.PREPROC_CHUNK_SIZE) )
                t.start()
                self.threads_map[ self.global_input_index ] = t
                self.global_input_index = list_end


        home_location = settings.SITE_PREFIX + '/'
        if 'HTTP_X_FORWARDED_HOST' in request.META:
            home_location = request.META['UWSGI_SCHEME'] + '://' + request.META['HTTP_X_FORWARDED_HOST'] + home_location

        context = {
        'PROCESSED_FRAME_CHUNKS': doneThreadCounter,
        'TOTAL_FRAME_CHUNKS': numberOfFrameChunks,
        'TOTAL_FRAMES': numberOfFrames,
        'HOME_LOCATION': home_location,
        }
        return render(request, 'pipeline_status.html', context)


    @method_decorator(login_required)
    @method_decorator(require_POST)
    def clear_backend(self, request):
        """
            API function that clear the data files used by the backend service.
            Arguments:
               request: request object containing details of the user session, etc.
        """

        if ('input_type' not in request.POST) or (request.POST['input_type'] not in ['positive', 'negative']):
            message = 'The input type descriptor is missing or invalid. The clearing cannot be started.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context = {'REDIRECT_TO': redirect_to, 'MESSAGE': message } )

        if not self.cpuvisor_srv_enabled:
            message = 'Only the caffe engine pipeline is currently supported. The clearing cannot be started.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context = {'REDIRECT_TO': redirect_to, 'MESSAGE': message } )

        clear_backend_type = request.POST['input_type']
        feats_file = self.DATASET_FEATS_FILE
        file_with_list_of_paths =  self.DATASET_IM_PATHS
        if clear_backend_type == 'negative':
            feats_file = self.NEG_FEATS_FILE
            file_with_list_of_paths =  self.NEGATIVE_IM_PATHS

        if not feats_file:
            message = 'The positive/negative feature files of the engine are not properly set. The clearing cannot be started.'
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context = {'REDIRECT_TO': redirect_to, 'MESSAGE': message } )

        try:
            if clear_backend_type=='negative':
                # there is only one negative features file
                os.remove(feats_file)
            else:
                # there can be several positive features files, so search
                # for them and remove them all
                path, filename = os.path.split(feats_file)
                filename = filename.replace('.','*.')
                for fl in glob.glob( os.path.join(path,filename) ):
                    os.remove(fl)
            if os.path.exists(file_with_list_of_paths):
                os.remove(file_with_list_of_paths)
        except Exception as e:
            message = 'There was an error while clearing the backend. Exception: ' + str(e)
            redirect_to = settings.SITE_PREFIX + '/admintools'
            return render_to_response("alert_and_redirect.html", context = {'REDIRECT_TO': redirect_to, 'MESSAGE': message } )

        message = 'The ' + clear_backend_type + ' backend data has been cleared!.'
        redirect_to = settings.SITE_PREFIX + '/admintools'
        return render_to_response("alert_and_redirect.html", context = {'REDIRECT_TO': redirect_to, 'MESSAGE': message } )
