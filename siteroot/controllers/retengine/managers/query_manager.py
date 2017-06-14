#!/usr/bin/env python

from multiprocessing import Manager
from multiprocessing import Pool

# for pickling of visor_engine method prior to sending to worker pool
import copy_reg
import types
import pickle
from retengine.utils import pickle_class_methods

from retengine import models
from retengine import query_translations

# initialise manager to create new shared memory area for the retrieval
manager = Manager()
visor_engine_process_func = None

class QueryWorker(object):
    """
        Query worker manager for the VISOR frontend.
        It keeps track of the query status and perform the serialization
        and de-serialization of the query results.
    """

    def __init__(self, query, visor_engine, on_cache_exclude_list):
        """
            Initializes the worker.
            Arguments:
                query: query in dictionary form
                visor_engine: visor engine object, which will execute the
                              query
                on_cache_exclude_list: boolean indicating if the query in
                                       on the list of excluded cached text
                                       queries.
        """
        # get a new query ID
        # print 'Generating a new query ID...'
        self.qid = visor_engine.get_query_id(query['engine'], query['dsetname'])
        self.query = query
        self.qindex = query_translations.get_qhash(query)
        # print 'Initializing query namespace...'
        self.shared_vars = manager.Namespace()

        # configure initial shared memory namespace values
        self.shared_vars.state = models.opts.states.processing
        self.shared_vars.postrainimg_paths = []
        self.shared_vars.curatedtrainimgs_paths = []
        self.shared_vars.negtrainimg_count = 0
        self.shared_vars.exectime_processing = 0.0
        self.shared_vars.exectime_training = 0.0
        self.shared_vars.exectime_ranking = 0.0
        self.shared_vars.err_msg = ''

        # define pickleable visor_engine function for processing
        global visor_engine_process_func
        copy_reg.pickle(types.MethodType,
                        pickle_class_methods._pickle_method,
                        pickle_class_methods._unpickle_method)

        # NOTE: The pickling fails if the query has been excluded (unselected) from the
        #       list of cached text queries, probably because its session seems to have
        #       been removed from memory
        try:
            if not on_cache_exclude_list:
                visor_engine_process_func = pickle.loads(pickle.dumps(visor_engine.process))
        except Exception as e:
            print e
            pass


    def get_status(self):
        """
            Gets the current status of the query.
            Returns:
                A QueryStatus object.
        """
        return models.QueryStatus(qid=self.qid,
                                  query=self.query,
                                  state=self.shared_vars.state,
                                  postrainimg_paths=self.shared_vars.postrainimg_paths,
                                  curatedtrainimgs_paths=self.shared_vars.curatedtrainimgs_paths,
                                  negtrainimg_count=self.shared_vars.negtrainimg_count,
                                  exectime_processing=self.shared_vars.exectime_processing,
                                  exectime_training=self.shared_vars.exectime_training,
                                  exectime_ranking=self.shared_vars.exectime_ranking,
                                  err_msg=self.shared_vars.err_msg)



class QueryManager(object):
    """
        Query manager for the VISOR frontend.
        Starts the query, retrieves the query status and results.
        It interfaces and keeps track of each worker assigned to each
        query.
    """

    def __init__(self, engine_class, visor_opts,
                 compdata_cache, result_cache,
                 process_pool,
                 proc_opts=models.param_sets.VisorEngineProcessOpts()):
        """
            Initializes the manager.
            Arguments:
                engine_class: visor engine object, which will execute the
                              query
                visor_opts: current configuration of options for the visor frontend.
                compdata_cache: Computational data cache manager
                result_cache: Results cache manager
                process_pool: pool of workers for multithreading processing
                proc_opts: current configuration of options for the visor engine.
        """
        self.process_pool = process_pool
        self._proc_opts = proc_opts
        self.result_cache = result_cache

        # dictionary for keeping track of active workers
        self._workers = {}

        # initialize engine
        self._engine = engine_class(visor_opts, compdata_cache, self.result_cache)


    def _get_worker_from_definition(self, query):
        """
            Gets the worker instance assigned to a query.
            Arguments:
                query: query in dictionary form.
            Returns:
                A QueryWorker object
        """
        qindex = query_translations.get_qhash(query)
        for key, value in self._workers.items():
            if value.qindex == qindex:
                return value


    def start_query(self, query,
                    user_ses_id=None, force_new_worker=False):
        """
            Starts a new worker and return its status (or if the worker
            already exists, return its status directly).
            Arguments:
                query: query in dictionary form.
                user_ses_id: user session id.
                force_new_worker: Boolean instructing this function to
                                  mandatorily create a new worker for the
                                  query.
            Returns:
                A QueryStatus object.
        """
        # start a query only if an existing query of the same name does not exist
        worker = None
        qindex = query_translations.get_qhash(query)
        for key, value in self._workers.items():
            if value.qindex == qindex:
                if not force_new_worker:
                    # return the already created worker
                    worker = value
                else:
                    # if force_new_worker is True, create a new worker
                    # for the same qhash and remove the previous one
                    del self._workers[key]
                break

        if not worker:
            # determine if on cache exclude list
            excl_query = self.result_cache[ query['engine'] ].query_in_exclude_list(query, ses_id=user_ses_id)

            # print 'Initializing query worker process...'
            worker = QueryWorker(query, self._engine, excl_query)
            self._workers[worker.qid] = worker

            # start the query
            # print 'Launching query process...'
            self.process_pool.apply_async(func=self._engine.process,
                                          args=(query,
                                                worker.qid,
                                                worker.shared_vars,
                                                self._proc_opts,
                                                user_ses_id))
        # return query status (including qid as a field)
        return worker.get_status()


    def get_query_status(self, qid):
        """
            Returns status of the worker specified by a Query ID.
            Arguments:
                qid: query id
            Returns:
                A QueryStatus object.
                It will raise a QueryIdError if there is no worker
                associated to the specified id.
        """
        if qid in self._workers:
            return self._workers[qid].get_status()
        else:
            raise models.errors.QueryIdError('Query ID %d is invalid' % qid)


    def get_query_status_from_definition(self, query):
        """
            Returns the status of the query specified by a (query, qtype,
            dsetname) tuple.
            Arguments:
                query: query in dictionary form.
            Returns:
                A QueryStatus object, or 'None' if there is no worker associated
                to the query.
        """
        worker = self._get_worker_from_definition(query)
        if worker:
            return worker.get_status()
        else:
            return None


    def get_query_result(self, status):
        """
            Returns the results of a query executed by the engine, and then
            frees the associated worker.
            Arguments:
                status: A QueryStatus object, associated with the query
                        for which the results are begin extracted.
            Returns:
                The list of results. Each element in the list will contain
                the path to an image but it might also contain information
                such as the ROI, annotation type, etc.
                It raises a ResultReadError if there is a problem getting
                the query result.
        """
        if not isinstance(status, models.QueryStatus):
            raise ValueError('status must be of type models.QueryStatus')

        engine = self._workers[status.qid].query['engine']
        rlist = self._engine.release_query_id_and_return_results(engine, status.qid)

        # free worker
        del self._workers[status.qid]

        return rlist
