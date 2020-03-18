#!/usr/bin/env python

from retengine.models import opts, query_data, param_sets, errors
from retengine import query_translations
from retengine.engine.visor_engine import VisorEngine

# initialise manager to create new shared memory area for the retrieval
from multiprocessing import Manager
manager = Manager()

# for pickling of visor_engine method prior to sending to worker pool
def call_it(instance, name, args=(), kwargs=None):
    """ Indirect caller for instance methods and multiprocessing """
    if kwargs is None:
        kwargs = {}
    return getattr(instance, name)(*args, **kwargs)

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
        # print ('Generating a new query ID...')
        self.qid = visor_engine.get_query_id(query['engine'], query['dsetname'])
        self.query = query
        self.qindex = query_translations.get_qhash(query)
        # print ('Initializing query namespace...')
        self.shared_vars = manager.Namespace()

        # configure initial shared memory namespace values
        self.shared_vars.state = opts.States.processing
        self.shared_vars.postrainimg_paths = []
        self.shared_vars.curatedtrainimgs_paths = []
        self.shared_vars.negtrainimg_count = 0
        self.shared_vars.exectime_processing = 0.0
        self.shared_vars.exectime_training = 0.0
        self.shared_vars.exectime_ranking = 0.0
        self.shared_vars.err_msg = ''

    def get_status(self):
        """
            Gets the current status of the query.
            Returns:
                A QueryStatus object.
        """
        return query_data.QueryStatus(qid=self.qid,
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

    def __init__(self, visor_opts,
                 compdata_cache, result_cache,
                 process_pool,
                 proc_opts= param_sets.VisorEngineProcessOpts()):
        """
            Initializes the manager.
            Arguments:
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
        self._engine = VisorEngine(visor_opts, compdata_cache, self.result_cache)


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

        return None


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
            excl_query = self.result_cache[query['engine']].query_in_exclude_list(query, ses_id=user_ses_id)

            # print ('Initializing query worker process...')
            try:
                worker = QueryWorker(query, self._engine, excl_query)
                self._workers[worker.qid] = worker

                # start the query
                # print ('Launching query process...')
                self.process_pool.apply_async(func=call_it,
                                              args=(self._engine,
                                                    'process',
                                                    (query,
                                                     worker.qid,
                                                     worker.shared_vars,
                                                     self._proc_opts,
                                                     user_ses_id)
                                                    )
                                             )
            except errors.QueryIdError:
                # this exception is triggered by the constructor of QueryWorker
                # if the backend cannot be contacted
                return query_data.QueryStatus(state=opts.States.fatal_error_or_socket_timeout)

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
            raise errors.QueryIdError('Query ID %d is invalid' % qid)


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
        if not isinstance(status, query_data.QueryStatus):
            raise ValueError('status must be of type query_data.QueryStatus')

        engine = self._workers[status.qid].query['engine']
        rlist = self._engine.release_query_id_and_return_results(engine, status.qid)

        # free worker
        del self._workers[status.qid]

        return rlist
