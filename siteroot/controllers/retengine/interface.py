#!/usr/bin/env python

import os
import shutil
import models
import managers
import query_translations

class VisorInterface(object):
    """
        Interface to the VISOR backend
        Calls VISOR backend via visor_engine module.
    """

    def __init__(self, engine_class,
                 predefined_ranklistpath, ranklistpath,
                 compdata_paths,
                 process_pool,
                 metadata_handler,
                 proc_opts=models.param_sets.VisorEngineProcessOpts(),
                 opts=models.param_sets.VisorOptions()):
        """
            Initializes the interface, the cache of each engine, and the query manager
            needed to process queries.
            Arguments:
                engine_class: instance of VisorEngine, used
                             for all interactions with the backend.
                predefined_ranklistpath: Path to folder with predefined ranking lists
                ranklistpath: Path to folder with ranking lists
                compdata_paths: instance of CompDataPaths, used
                                to handle all folder/files in the computational data
                                folders
                process_pool: instance of CpProcessPool, used to support multi-threading
                metadata_handler: instance of MetaDataHandler, used to access the
                                  metadata of a dataset
                proc_opts: used for access to the configuration of the VISOR engine
                opts: used for access to the configuration of the VISOR frontend
        """
        self.engine_class = engine_class
        self.process_pool = process_pool
        self.proc_opts = proc_opts
        self.opts = opts
        self.metadata_handler = metadata_handler

        # set which result caches should be enabled to temporary variables
        if proc_opts.disable_cache:
            enabled_result_caches = managers.ResultCache.CacheCfg.query_ses_only
            enabled_result_excl_caches = managers.ResultCache.CacheCfg.query_ses_only
        else:
            enabled_result_caches = managers.ResultCache.CacheCfg.all
            enabled_result_excl_caches = managers.ResultCache.CacheCfg.query_ses_only

        # initialize caches
        self.result_cache = {}
        for engine in self.opts.engines_dict:
            engine_ranklistpath = os.path.join(ranklistpath, engine)
            engine_predefined_ranklistpath = os.path.join(predefined_ranklistpath, engine)
            self.result_cache[engine] = managers.ResultCache(engine_predefined_ranklistpath,
                                                             engine_ranklistpath,
                                                             self.process_pool,
                                                             enabled_caches=enabled_result_caches,
                                                             enabled_excl_caches=enabled_result_excl_caches)

        self.compdata_cache = managers.CompDataCache(compdata_paths,
                                                     self.opts.engines_dict,
                                                     proc_opts.disable_cache)

        # create query manager to run queries
        self.query_manager = managers.QueryManager(engine_class,
                                                   opts,
                                                   self.compdata_cache,
                                                   self.result_cache,
                                                   self.process_pool,
                                                   proc_opts)


    def is_backend_available(self):
        """
            Checks whether the backend engines are running or not.
            Returns:
                True, only if ALL configured backend engines are reachable.
                It returns False otherwise.
        """
        backends_available = len(self.opts.engines_dict) > 0
        for engine in self.opts.engines_dict:
            backends_available = backends_available and self.engine_class.check_backend_is_reachable(self.opts.engines_dict[engine]['backend_port'])
        return backends_available


    # ----------------------------------
    ## Routines for query execution
    #      + All return an instance of models.QueryData
    #      + `query' should be called first, and will return results directly
    #             if they are cached in the rlists field of query data,
    #             otherwise only the status field of QueryData will be populated
    #      + once `query' has been called once, it can be called repeatedly to
    #             monitor the status of a query, but it's more efficient to
    #             call `continue_query' instead with the query's assigned ID
    #             (available in QueryData.status.qid). Every time, a blank results
    #             field will be returned along with an updated status field
    #             until status becomes `results_ready' after which the results field
    #             will automatically be populated with the results and the query
    #             finalized (if `return_rlist_directly' is TRUE)
    #      + `query_ses_id' is an optional parameter which is a unique identifier
    #             for the currently running query. This is passed onto self.result_cache
    #             and is used only if the `query_session_cache' cache type is being
    #             used to store cached results only for the current query
    #      + `user_ses_id' is an optional parameter which is a unique identifier
    #             for the current user session. This is passed onto query_manager,
    #             and then onto engine, and used to check the exclude status (among
    #             possibly other things) of the query in result_cache and (within
    #             engine when saving and loading computational data files) in compdata_cache
    # ----------------------------------

    def query(self, query, return_rlist_directly=True,
              query_ses_id=None, user_ses_id=None):
        """
            Gets the results of a query (if cached), else starts a new query worker
            and return its status
            Arguments:
                return_rlist_directly: If TRUE, as soon as worker status becomes
                                       'results ready', the ranking list is returned. Otherwise,
                                        a further call to 'query' will be required to retrieve results.
                query_ses_id: Query session ID
                user_ses_id: User session ID
            Returns:
                An instance of QueryData, containing the status of the query and the list
                of results associated with it.
        """

        if query['qtype'] == models.opts.Qtypes.text and query['qdef'].startswith('keywords:'):

            keywords = query['qdef'].replace('keywords:', '')
            training_images = []
            rlist = []
            for key in keywords.split(','):
                keyword_matches = self.metadata_handler.get_files_by_keyword(key, query['dsetname'])
                training_images = set().union(keyword_matches, training_images)
            for img in training_images:
                rlist.append({'path': img})
            status = models.QueryStatus(state=models.opts.States.results_ready)
            return models.QueryData(status, rlist)

        else:
            # get results directly from cache if possible
            rlist = self.result_cache[query['engine']].get_results(query, query_ses_id, user_ses_id)

            if rlist:
                # *** READ RESULTS IN FROM CACHE ***
                status = models.QueryStatus(state=models.opts.States.results_ready)
            else:
                # *** READ STATUS/RESULTS IN FROM WORKER ***
                # otherwise, try returning an existing query instance if possible ...
                status = self.query_manager.get_query_status_from_definition(query)
                if not status:
                    # ... or return a new one
                    status = self.query_manager.start_query(query, user_ses_id)

                # if the query is not in cache and finished with a fatal error, maybe it is being retried
                # after a change in the settings. Give it a chance to run again without fully restarting
                # the server
                if status.state == models.opts.States.fatal_error_or_socket_timeout:
                    print 'WARNING: Re-executing a previously failed query by fatal-error or timeout'
                    status = self.query_manager.start_query(query, user_ses_id, force_new_worker=True)

                if return_rlist_directly and status.state == models.opts.States.results_ready:
                    try:
                        rlist = self._get_results(status, query_ses_id, user_ses_id)
                    except models.errors.ResultReadError:
                        status = models.QueryStatus(state=models.opts.States.result_read_error)

            return models.QueryData(status, rlist)


    def continue_query(self, qid, return_rlist_directly=True,
                       query_ses_id=None, user_ses_id=None):
        """
            Continues the execution of an existing query.
            Arguments:
                qid: ID of the query being continued.
                return_rlist_directly: If TRUE, as soon as worker status becomes
                                       'results ready', the ranking list is returned. Otherwise,
                                        a further call to 'query' will be required to retrieve results.
                query_ses_id: Query session ID
                user_ses_id: User session ID
            Returns:
                An instance of QueryData, containing the status of the query and the list
                of results associated with it.
        """
        rlist = None
        try:
            status = self.query_manager.get_query_status(qid)
        except models.errors.QueryIdError:
            # set error in status if Query ID doesn't exist
            status = models.QueryStatus(state=models.opts.States.invalid_qid)

        # *** READ RESULTS IN FROM WORKER IF DONE ***
        if return_rlist_directly and status.state == models.opts.States.results_ready:
            try:
                rlist = self._get_results(status, query_ses_id, user_ses_id)
            except models.errors.ResultReadError:
                status = models.QueryStatus(state=models.opts.States.result_read_error)

        return models.QueryData(status, rlist)


    def _get_results(self, status, query_ses_id=None, user_ses_id=None):
        """
            Get the results of a query and also saves them to the results
            cache.
            If should only be used with queries whose status is
            models.opts.States.results_ready.
            Arguments:
                status: Instance of QueryStatus, used to check is query
                        results are ready.
                query_ses_id: Query session ID
                user_ses_id: User session ID
            Returns:
                The list of results for the query.
                Raises a ResultReadError if the status is wrong, or there is a problem
                reading from the backend.
        """
        # ensure we are reading from query with correct state
        if status.state is not models.opts.States.results_ready:
            raise models.errors.ResultReadError('Query must have results to read!')

        # read in results
        rlist = self.query_manager.get_query_result(status)

        # save results to cache
        if rlist:
            self.result_cache[status.query['engine']].add_results(rlist, status.query,
                                                                  query_ses_id,
                                                                  user_ses_id)

        return rlist


    # ----------------------------------
    ## Routines for cache management
    # ----------------------------------

    def get_cached_text_queries(self, user_ses_id=None):
        """
            Returns a list of tuples with all text queries.
            Arguments:
                user_ses_id: User session ID
            Returns:
                A list of tuples, where the first entry of each tuple is
                the text query itself, and the second entry is True
                if the query is currently in the cache exclude list.
        """
        querystrs = {}
        q_excl_list = {}
        query_tuples = {}
        for engine in self.opts.engines_dict:
            querystrs[engine] = self.result_cache[engine].get_all_disk_cached_text_querystrs()
            # sort text queries alphabetically
            querystrs[engine].sort()
            # get cache exclude list
            q_excl_list[engine] = []
            for querystr in querystrs[engine]:
                for dataset in self.opts.datasets:
                    query = query_translations.querystr_tuple_to_query(querystr, models.opts.Qtypes.text, dataset, engine)
                    q_excl_list[engine].append(self.result_cache[engine].query_in_exclude_list(query, ses_id=user_ses_id))
            # zip
            query_tuples[engine] = zip(querystrs[engine], q_excl_list[engine])
            ##print 'Cached text queries returned: %s' % query_tuples[engine]

        return query_tuples


    def set_text_query_cache_exclude_list(self, excl_list, user_ses_id=None):
        """
            Sets the text queries marked as excluded
            Arguments:
                excl_list: List of queries to be excluded
                user_ses_id: User session ID
        """
        self.compdata_cache.clear_query_exclude_list(ses_id=user_ses_id)
        for engine in self.opts.engines_dict:
            self.result_cache[engine].clear_query_exclude_list(ses_id=user_ses_id)
            for querystr in excl_list[engine]:
                for dataset in self.opts.datasets:
                    query = query_translations.querystr_tuple_to_query(querystr, models.opts.Qtypes.text, dataset, engine)
                    self.compdata_cache.add_query_to_exclude_list(query, ses_id=user_ses_id)
                    self.result_cache[engine].add_query_to_exclude_list(query, ses_id=user_ses_id)

        ##print 'Set text query exclude list: %s' % excl_list


    def delete_text_query(self, querystr, engine):
        """
            Deletes a specific text query related to the specified engine,
            for all available datasets.
            The query is deleted from the results cache and also
            from all computational data caches.
            Arguments:
                excl_list: List of queries to be excluded
                user_ses_id: User session ID
        """
        for dataset in self.opts.datasets:

            query = query_translations.querystr_tuple_to_query(querystr, models.opts.Qtypes.text, dataset, engine)

            self.compdata_cache.delete_compdata(query)
            self.result_cache[engine].delete_results(query, for_all_datasets=True)

            #NOTE: In the future, if there is a curated version of the query in the cache, remove it as well.
            #      This is disable until really needed
            #query_curated = query_translations.querystr_tuple_to_query('#' + querystr, models.opts.Qtypes.text, dataset, engine)
            #self.result_cache[engine]._mem_cache.delete_results(query_curated, for_all_datasets=True)

            ##print 'Deleted cached text query: %s' % query


    def clear_cache(self, cache_type):
        """
            Clears all entries in the specified cache type
            Arguments:
                type: indicates the cache type. Possible values are
                'features', 'annotations, 'classifiers', 'postrainimgs'
                and 'ranking_lists'
        """
        # if clearing cache by query type ....
        if cache_type in ['text', 'image']:
            self.compdata_cache.clear_features_cache(cache_type)
            self.compdata_cache.clear_annotations_cache(cache_type)
            self.compdata_cache.clear_classifiers_cache(cache_type)
            self.compdata_cache.clear_postrainimgs_cache(cache_type)
            for engine in self.opts.engines_dict:
                self.result_cache[engine].clear_all_caches(cache_type)
        else:
            #... or if clearing cache by type of computational data
            if cache_type == 'features':
                self.compdata_cache.clear_features_cache()
            elif cache_type == 'annotations':
                self.compdata_cache.clear_annotations_cache()
            elif cache_type == 'classifiers':
                self.compdata_cache.clear_classifiers_cache()
            elif cache_type == 'postrainimgs':
                self.compdata_cache.clear_postrainimgs_cache()
            elif cache_type == 'ranking_lists':
                for engine in self.opts.engines_dict:
                    self.result_cache[engine].clear_all_caches()


    def set_cache_disabled(self, disabled):
        """
            Disables/Enables all caches.
            Arguments:
                disabled: Boolean set to True to disable the caches
                          or set to False to enable them.
        """
        self.proc_opts.disable_cache = disabled

        self.compdata_cache.disable_cache = disabled
        if disabled:
            for engine in self.opts.engines_dict:
                self.result_cache[engine].enabled_caches = managers.ResultCache.CacheCfg.query_ses_only
        else:
            for engine in self.opts.engines_dict:
                self.result_cache[engine].enabled_caches = managers.ResultCache.CacheCfg.all


    # ----------------------------------
    ## Routines for manipulating uber classifiers
    # ----------------------------------

    def save_uber_classifier(self, query, name):
        """
            Saves an uber classifier to the results cache
            and all computational data caches.
            Arguments:
                query: the query to be saved, in dictionary form.
                name: the name to be given to the classifier.
        """
        ucquery = query_translations.querystr_tuple_to_query('$' + name,
                                                             models.opts.Qtypes.text,
                                                             query['dsetname'],
                                                             query['engine'])

        # there is a classifier file and a ranking file, but they are associated
        # with the current query name. If query is an image query, it has a
        # random name. So, save the current files with the name of the uber
        # classifier to be able to find these files later.

        src_classifier_fname = self.compdata_cache._get_classifier_fname(query)
        src_ranking_fname = self.result_cache[query['engine']]._get_disk_fname(query)

        dst_classifier_fname = self.compdata_cache._get_classifier_fname(ucquery)
        dst_ranking_fname = self.result_cache[query['engine']]._get_disk_fname(ucquery)

        ##print 'Creating uber classifier: $%s...' % name

        try:
            # save the classifier file ... if it exists
            if os.path.exists(src_classifier_fname):
                shutil.copy(src_classifier_fname, dst_classifier_fname)

            # save the ranking file ... this one should exist
            shutil.copy(src_ranking_fname, dst_ranking_fname)
        except IOError as e:
            print 'IOError while saving uber classifier: ', e
            return False

        return True


    # ----------------------------------
    ## Routines for displaying training images and retraining
    # ----------------------------------

    def get_training_images(self, query, user_ses_id=None):
        """
            Retrieves the list of training images associated to a query
            Arguments:
                query: the query associated to the training images,
                       in dictionary form.
                user_ses_id: User session ID.
            Returns:
                A list of training images entries. Each entry consists of
                the path to the training image an a variable indicating
                whether the image was used as a positive or negative image,
                or if it was ignored.
        """
        return self.compdata_cache.get_training_images(query,
                                                       user_ses_id=user_ses_id)
