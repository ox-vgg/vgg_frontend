from visorgen import settings
import retengine
import dsetmap
import utils
from PIL import Image
from PIL import ImageDraw
import json
import traceback
import sys
import urllib
import os
from threading import Lock
import time

class VisorController:
    """ Base class for the VISOR frontend controller """

    def __init__(self, engine_class):
        """
            Initializes the controller.
            Arguments:
                engine_class: instance of VisorEngine - used
                              for all interactions with the backend.
        """
        cfg_paths = settings.PATHS
        cfg_metadata = settings.METADATA
        cfg_imsearchtools = settings.IMSEARCHTOOLS
        cfg_retengine = settings.RETENGINE
        cfg_visor = settings.VISOR

        self.compdata_paths = retengine.models.param_sets.CompDataPaths(**cfg_paths)
        self.metadata_paths = retengine.models.param_sets.MetaDataPaths(**cfg_metadata)
        self.proc_opts = retengine.models.param_sets.VisorEngineProcessOpts(**cfg_retengine)
        self.proc_opts.imsearchtools_opts = cfg_imsearchtools

        self.opts = retengine.models.param_sets.VisorOptions(**cfg_visor)

        # initialize pools
        self.process_pool = utils.cp_work_pools.CpProcessPool(self.proc_opts.pool_workers)
        self.process_pool.start()
        # NOTE: so far, there's no need to stop() or terminate() as the
        #       threads (not processes, see comments on CpProcessPool)
        #       are killed when the server is shutdown or restarted
        self.query_available_lock = Lock()

        # initialize query cache for storing ongoing query definition dicts
        # by query session id
        self.query_key_cache = retengine.managers.QueryKeyCache()

        # initialize interface class for all interactions
        self.interface = retengine.VisorInterface(engine_class,
                                                  cfg_paths['rankinglists'],
                                                  self.compdata_paths,
                                                  self.process_pool,
                                                  self.proc_opts,
                                                  self.opts)

        # initialize class for metadata extraction
        self._meta_extr = dsetmap.metaConverter.fnameToMetaConverter(self.opts.datasets,
                                                                     self.metadata_paths.metadata)

        # initialize classes for pagination
        self._page_manager = utils.pagination.PageManager(self.opts.results_per_page)

    def set_config(self, kwargs, user_session_id):
        """
            Sets parts of the frontend/backend configuration.
            Only admin should be able to execute this. Be sure to restrict
            access to this from the home frontend.
            Arguments:
                kwargs: Dictionary of configuration settings
                user_session_id: User session id.
        """
        kwargs = dict(kwargs) # convert QueryDict to dict before going forward
        if 'num_pos_train' in kwargs:
            try:
                num_pos_train = int(kwargs['num_pos_train'][0])
            except ValueError:
                num_pos_train = -1

            if num_pos_train > 200:
                num_pos_train = 200
            if num_pos_train < 1:
                num_pos_train = -1

            if num_pos_train > 0:
                self.proc_opts.imsearchtools_opts['num_pos_train'] = num_pos_train

        if 'improc_timeout' in kwargs:
            try:
                improc_timeout = float(kwargs['improc_timeout'][0])
            except ValueError:
                improc_timeout = -1.0

            if improc_timeout > 0.0:
                self.proc_opts.imsearchtools_opts['improc_timeout'] = improc_timeout

        if 'improc_engine' in kwargs:
            improc_engine = kwargs['improc_engine'][0]
            self.proc_opts.imsearchtools_opts['engine'] = improc_engine

        if 'rf_rank_type' in kwargs:
            rf_rank_type = kwargs['rf_rank_type'][0]
            self.proc_opts.rf_rank_type = rf_rank_type

        if 'rf_rank_topn' in kwargs:
            rf_rank_topn = int(kwargs['rf_rank_topn'][0])
            self.proc_opts.rf_rank_topn = rf_rank_topn

        if 'rf_train_type' in kwargs:
            rf_train_type = kwargs['rf_train_type'][0]
            self.proc_opts.rf_train_type = rf_train_type

        if 'cache_disabled' in kwargs:
            disable_cache = bool(int(kwargs['cache_disabled'][0]))
            self.interface.set_cache_disabled(disable_cache)

        inactive_text_queries = {}
        # SET text query exclude list for each engine
        for engine in self.opts.engines_dict:
            engine_active_text_queries_LABEL = 'active_text_queries_' + engine
            engine_all_text_queries_LABEL  = 'all_text_queries_' + engine
            if engine_active_text_queries_LABEL in kwargs:
                # get list of active (checked) text queries from the form
                active_text_queries = kwargs[ engine_active_text_queries_LABEL ]
                if not isinstance(active_text_queries, list):
                    active_text_queries = [active_text_queries]
                active_text_queries = map(lambda s: s.encode('GB18030'), active_text_queries)

                if engine_all_text_queries_LABEL not in kwargs:
                    raise RuntimeError( engine_all_text_queries_LABEL + ' field not found in response')

                # get complete list of all text queries from the form (hidden field)
                all_text_queries = kwargs[ engine_all_text_queries_LABEL ]
                if not isinstance(all_text_queries, list):
                    all_text_queries = [all_text_queries]
                all_text_queries = map(lambda s: s.encode('GB18030'), all_text_queries)

                # remove the intersection to get the list of inactive queries
                inactive_text_queries[engine] = [item for item in all_text_queries
                                                if item not in active_text_queries]

                # Detect if the cache of a query was enable and now is going to be disable.
                # In such a case, cleanup the unused postrainimgs for that particular query,
                # in preparation for the download of new images
                try:
                    for txt in kwargs[ engine_all_text_queries_LABEL ]:
                        for dataset in self.opts.datasets:
                            query = {'qdef': txt, 'engine' : engine, 'qtype': 'text', 'dsetname': dataset } # This should only work for text queries
                            if (txt in inactive_text_queries[engine]) and (not self.interface.compdata_cache.query_in_exclude_list(query, ses_id=user_session_id)):
                                self.interface.compdata_cache.cleanup_unused_query_postrainimgs_cache(query)
                except Exception, e:
                       print e
                       pass

            else:
                if engine_all_text_queries_LABEL in kwargs:
                    inactive_text_queries[engine] = kwargs[ engine_all_text_queries_LABEL ]
                    # Detect if the cache of a query was enable and now is going to be disable.
                    # In such a case, cleanup the unused postrainimgs for that particular query,
                    # in preparation for the download of new images
                    for txt in kwargs[ engine_all_text_queries_LABEL ]:
                        for dataset in self.opts.datasets:
                            query = {'qdef': txt, 'engine' : engine, 'qtype': 'text', 'dsetname': dataset} # This should only work for text queries
                            if (txt in inactive_text_queries[engine]) and (not self.interface.compdata_cache.query_in_exclude_list(query, ses_id=user_session_id)):
                                self.interface.compdata_cache.cleanup_unused_query_postrainimgs_cache(query)
                else:
                    inactive_text_queries[engine] = []

        # update the query cache exclude list
        self.interface.set_text_query_cache_exclude_list(inactive_text_queries, user_ses_id=user_session_id)


    def get_image(self, path, roi=None, as_thumbnail=False):
        """
            Returns an image from the server
            Arguments:
                path: Full path to the image to be returned, possibly with ROI information
                roi: Boolean indicating whether to return the image with the ROI drawn on it, as long
                     the ROI information is provided in the path.
                as_thumbnail: Boolean indicating whether to scale down the image to the size of a
                              thumbnail.
            Returns: an image
        """
        try:
            img = Image.open(path)
            scale = 1
            if as_thumbnail:

                imW, imH = img.size
                maxW = 200
                maxH = 200
                maxW = float(maxW)
                maxH = float(maxH)

                if maxW == None and maxH == None:
                    scale = 1
                else:
                    if maxW == None:
                        scale = maxH/imH
                    elif maxH == None:
                        scale = maxW/imW
                    else:
                        scale = min(maxH/imH, maxW/imH)

                if scale<1:
                    img.thumbnail((int(imW*scale), int(imH*scale)))
                else:
                    scale = 1

                if (img.mode != 'RGB'):
                    img = img.convert('RGB');

            if roi:

                values = [float(val)*scale for val in roi['roi'].split('_')]
                points = []
                for i in range(1, len(values), 2):
                    points.append( (values[i-1], values[i]) )

                if 'roi_colour' in roi:
                    r, g, b = [int(x) for x in  roi['roi_colour'].split('_')]
                else:
                    r, g, b = 255, 255, 0
                linecol = (r,g,b)

                if 'roi_linewidth' in roi:
                    linewidth = int(roi['roi_linewidth'])
                else:
                    linewidth = 5

                imd = ImageDraw.Draw(img)
                for i in range(0, len(points)-1):
                    imd.line( (points[i][0], points[i][1], points[i+1][0], points[i+1][1]), fill=linecol, width=linewidth );

            return img

        except IOError:

            print 'Exception while reading ' + path
            img = Image.new('RGBA', (1, 1), (255,0,0,0))
            return img


    def check_query_in_cache_no_locking(self, query, user_session_id):
        """
            Checks whether a query is cached or not. No locking between threads is done.
            Arguments:
                query: dictionary from of the query being checked
                user_session_id: User session id
            Returns: boolean indicating whether a query is cached or not.
        """
        rlist = self.interface.result_cache[ query['engine'] ].get_results(query, query_ses_id=None, user_ses_id=user_session_id)

        return bool(rlist)


    def check_query_in_cache_with_locking(self, query, user_session_id):
        """
            Checks whether a query is cached or not.
            If another thread arrives to this method while a previous thread is running the
            same query, the arriving thread will wait until the query is finished to return
            the output of this method.
            Arguments:
                query: dictionary from of the query being checked
                user_session_id: User session id
            Returns: boolean indicating whether a query is cached or not
        """
        try:
            # lock
            self.query_available_lock.acquire()
            # check if it in the cache
            rlist = self.interface.result_cache[ query['engine'] ].get_results(query, query_ses_id=None, user_ses_id=user_session_id)
            if rlist==None:
                # if not cached, check the status to verify that is not being executed by another thread
                status = self.interface.query_manager.get_query_status_from_definition(query)
                while (status != None and status.state <= retengine.models.opts.states.results_ready):
                    # if it is begin executed, wait a bit and then query the status again ...
                    time.sleep(1)
                    status = self.interface.query_manager.get_query_status_from_definition(query)
                    if status != None and status.state==retengine.models.opts.states.results_ready:
                        # if ready, get the results and leave the loop
                        rlist = self.interface.result_cache[ query['engine'] ].get_results(query, query_ses_id=None, user_ses_id=user_session_id)
            return bool(rlist)
        finally:
            # unlock
            self.query_available_lock.release()

        return False


    def create_query_session(self, query, user_session_id):
        """
            Starts a new query session and returns a dictionary describing it.
            Arguments:
                query: dictionary from of the query being checked
                user_session_id: User session id
            Returns: A dictionary in the form:
                {
                'query_ses_id': identifier for the query in the query key cache,
                'cached': True if the result was in the result cache and needs no further processing, False otherwise.
                }
        """
        # generate a new query_ses_id to either act as a lookup for a cached
        # query, or identifier for a new query which will be processed by
        # execquery
        query_ses_id = self.query_key_cache.gen_query_session_id(query)

        # either get progress of query or its result
        query_data = self.interface.query(query, user_ses_id=user_session_id)

        return {'query_ses_id': query_ses_id, 'cached': bool(query_data.rlist)}


    def get_query_result(self, query, user_session_id, query_ses_id=None):
        """
            Retrieves the results of a query.
            Arguments:
                query: dictionary from of the query being checked
                user_session_id: user session id
                query_ses_id: query id
            Returns: An instance of the QueryData class.
        """
        # try to get the result of a query
        query_data = self.interface.query(query,
                                          query_ses_id=query_ses_id,
                                          user_ses_id=user_session_id)

        return query_data


    def is_backend_reachable(self):
        """
            Check whether the backend services are running and reachable.
            Returns: The string representation of a boolean indicating whether
                     the backend services are reachable or not. "0" represents
                     False.
        """
        return str(int(self.interface.is_backend_available()))


    def execquery_impl(self, qsid, user_session_id, return_rlist_directly=False):
        """
            Implementation of callback function for executing query.
            Launches a new process pool to execute a query or, if a process pool
            already exists, checks it's status.
            Arguments:
                qsid: query id
                user_session_id: user session id
                return_rlist_directly: if TRUE as soon as QueryWorkers' status becomes
                 'results ready', the ranking list is returned. Otherwise,
                 a further call to 'query' will be required to retrieve teh results.
            Returns: An instance of the QueryData class.
        """
        # get query definition dict from query_ses_id
        (query, qid) = self.query_key_cache.get_query_details_and_qid(qsid)

        print 'IN EXECQUERY WITH QUERY DICT %s' % json.dumps(query)

        if qid is not None:
            # if a backend qid was read from the query key cache, use this to continue
            # an existing query in an efficient manner

            print 'CONTINUING QUERY WITH QID: ' + str(qid)
            query_data = \
                self.interface.continue_query(qid,
                                              return_rlist_directly=return_rlist_directly,
                                              query_ses_id=qsid,
                                              user_ses_id=user_session_id )
        else:
            # ELSE if no backend qid is associated with the current query session as yet
            # start a new query and then add the backend qid to the session data
            # for future calls to execquery

            print 'STARTING A NEW QUERY...'
            query_data = self.interface.query(query,
                                              return_rlist_directly=return_rlist_directly,
                                              query_ses_id=qsid,
                                              user_ses_id=user_session_id )
            self.query_key_cache.set_query_session_backend_qid(query_data.status.qid,
                                                               qsid)

        return query_data


    def uploadimage(self, file=None, url=None, img_data=None, is_data_base64=False):
        """
            Helper method to upload an image to the server, must likely be request of
            the user.
            Arguments:
                file: Path to the file, in case a local image is being uploaded.
                url: URL path to the file, in case the image has to be retrieved from an URL.
                img_data: In case the image data is being uploaded directly. This is to be
                          used in case the image is wrapped and sent directly from a GUI control.
                is_data_base64: Boolean indicating whether img_data is encoded in base64 or not.
            Returns:
                A JSON indicating the local image path after uploading and the url from where the
                image was downloaded.
        """
        filepath = locals()['file']  # convert file -> filepath to avoid python clash
        if filepath:
           print 'File received for upload: %s', filepath
        if url:
           print 'URL received for upload: %s', url

        imageuploader = \
            utils.imuptools.ImageUploader(self.compdata_paths.uploadedimgs,
                                          self.proc_opts.resize_width,
                                          self.proc_opts.resize_height)
        try:
            if filepath:
                localimg = imageuploader.get_localimg_from_file(filepath)
            elif url:
                localimg = imageuploader.get_localimg_from_url(url)
            elif img_data:
                localimg = imageuploader.get_localimg_from_imgdata(img_data, is_data_base64)
            else:
                raise RuntimeError('Neither file, url or data_buffer parameters were passed to uploadimage!')

        except Exception:
            traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2], limit=2)
            jsonstr = json.dumps({'Error': 'Error uploading image', 'srcurl': url, 'impath': filepath})
            return jsonstr

        localimg = urllib.quote(localimg)
        jsonstr = json.dumps({'impath': localimg, 'srcurl': url})
        return jsonstr


    def get_engines_urls(self):
        """
            Retrieves the urls of the backend engines. This to be
            able to include URL redirections to the backends from
            the frontend, whenever necessary.
            Returns: A Dictionary mapping engine-names to urls
        """
        urls = {}
        for engine in self.opts.engines_dict:
            urls[engine] = self.opts.engines_dict[engine]['url']
        return urls
