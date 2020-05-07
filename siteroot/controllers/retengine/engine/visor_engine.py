#!/usr/bin/env python

import traceback
import sys
import os

from retengine.models import param_sets, errors
from retengine.models.opts import RfRankTypes, States
from retengine.utils import timing
from retengine.managers import compdata_cache as compdata_cache_module
from retengine.engine import backend_client
from retengine.engine.qtypes import factory

# ----------------------------------
## Engine Class
# ----------------------------------

class VisorEngine(object):
    """
        Worker engine for VISOR backend

        Provides functions to:
        (a) check if backend is reachable
        (b) get a unique query id to identify a new query
        (c) process that query
        (d) free up resources related to that query and return results when done

        All using the lower-level interface provided by lib/backend_client module.

        Should be used via the interface module to allow it to be called in a
        multi-threaded way and provide result caching.
    """

    def __init__(self, visor_opts, compdata_cache, result_cache):
        """
            Initializes the engine.
            Arguments:
                visor_opts: current configuration of options for the visor frontend.
                compdata_cache: Computational data cache manager.
                result_cache: Results cache manager.
        """
        super(VisorEngine, self).__init__()

        if not isinstance(compdata_cache, compdata_cache_module.CompDataCache):
            raise ValueError('compdata_cache must be of type compdata_cache_module.CompDataCache')

        self.visor_opts = visor_opts
        # setup class for managing cache of images/classifiers etc.
        self.compdata_cache = compdata_cache
        # setup callbacks for compdata_cache
        self.compdata_cache.callbacks['save_classifier'] = self._save_classifier
        self.compdata_cache.callbacks['load_classifier'] = self._load_classifier
        self.compdata_cache.callbacks['save_annotations'] = self._save_annotations
        self.compdata_cache.callbacks['load_annotations_and_trs'] = self._load_annotations_and_trs
        self.compdata_cache.callbacks['get_annotations'] = self._get_annotations

        # store reference to result_cache class - used for reranking previously computed rlists
        self.result_cache = result_cache

    def __getstate__(self):
        """
            Returns a picklable object with class information for
            reconstructing the instance.
        """
        # serializing
        a_dict = dict(self.__dict__)
        return a_dict


    def __setstate__(self, a_dict):
        """
            Reconfigures the instance from the object specified in the parameter.
        """
        # deserializing
        self.__dict__.update(a_dict)


    def get_query_id(self, engine, dsetname):
        """
            Contacts the backend requesting a new Query ID.
            Returns a new unique query id which can be used with a
            subsequent call to process.
            Arguments:
                engine: backend engine to contact
                dsetname: dataset used for the query
            Returns:
                A positive integer number corresponding to the new query ID.
                It raises a QueryIdError if the ID is negative or 0.
        """
        ses = backend_client.Session(self.visor_opts.engines_dict[engine]['backend_port'])
        query_id = ses.get_query_id(dsetname)

        if query_id <= 0:
            raise errors.QueryIdError('Could not get a Query ID from VISOR backend')

        return query_id


    def process(self, query, query_id, shared_vars, opts, user_ses_id=None):
        """
            Executes a query using the VISOR backend
            Arguments:
                query: query in dictionary form.
                query_id: ID of the query
                shared_vars: holder of global shared variables
                opts: current configuration of options for the visor engine
                user_ses_id: user session id
            Returns:
                'None' in case of success, as the results are saved to the caches.
                It can raise several exceptions, depending on the error:
                    ValueError: In the presence of incorrect options
                    ClassifierTrainError: In case the training fails
                    Exception: In case of any other error
        """
        if not isinstance(opts, param_sets.VisorEngineProcessOpts):
            raise ValueError('opts must be of type param_sets.VisorEngineProcessOpts')

        backend_port = self.visor_opts.engines_dict[query['engine']]['backend_port']
        ses = backend_client.Session(backend_port)

        try:
            # check if classifier has been trained and saved to file or not
            if not self.compdata_cache.load_classifier(query,
                                                       query_id=query_id,
                                                       user_ses_id=user_ses_id):
                # if not try loading in precomputed annotations and features
                if not self.compdata_cache.load_annotations_and_trs(query,
                                                                    query_id=query_id,
                                                                    user_ses_id=user_ses_id):
                    # if both classifier and annotations could not be loaded, start
                    # computation from scratch now...

                    print ('Getting query handler for Query ID: %d' % query_id)
                    query_handler = factory.get_query_handler(query,
                                                             query_id,
                                                             backend_port,
                                                             self.compdata_cache,
                                                             opts)
                    print ('Computing features for Query ID: %d' % query_id)
                    shared_vars.exectime_processing = query_handler.compute_feats(shared_vars)

                    self.compdata_cache.save_annotations(query,
                                                         query_id=query_id,
                                                         user_ses_id=user_ses_id)
                # train classifier now if it hasn't been already
                print ('Training classifier for Query ID: %d' % query_id)
                shared_vars.state = States.training
                with timing.TimerBlock() as timer:
                    anno_path = None
                    # if the query is in the exclude list, specify the annotation path as it can be used in the backend
                    if self.result_cache[query['engine']].query_in_exclude_list(query, ses_id=user_ses_id):
                        anno_path = self.compdata_cache._get_annotations_fname(query)
                    error = ses.train(query_id, anno_path)
                    if error:
                        if isinstance(error, str):
                            error = error.encode('ascii')
                        raise errors.ClassifierTrainError('Could not train classifier. Backend response: ' + str(error))
                shared_vars.exectime_training = timer.interval

                # and save it to file
                self.compdata_cache.save_classifier(query,
                                                    query_id=query_id,
                                                    user_ses_id=user_ses_id)
            else:
                print ('Loaded classifier from file for Query ID: %d' % query_id)

            # compute ranking

            do_regular_rank = False

            if opts.rf_rank_type == RfRankTypes.full:
                # set flag to do regular ranking
                do_regular_rank = True

            elif opts.rf_rank_type == RfRankTypes.topn:
                if 'prev_qsid' in query:
                    # reranking of top n results from previous query

                    prev_qsid = query['prev_qsid']
                    topn = opts.rf_rank_topn
                    print ('Computing reranking of top %d results from previous query (%s) for Query ID %d' % (topn, prev_qsid, query_id))
                    # Look up ranking list for previous query (by query session ID)
                    prev_rlist = self.result_cache[query['engine']].get_results_from_query_ses_id(prev_qsid, user_ses_id)
                    # extract dataset string IDs for top N results from the ranking list
                    subset_ids = [ritem['path'] for ritem in prev_rlist[0:topn]]

                    with timing.TimerBlock() as timer:
                        ses.rank(query_id, subset_ids)
                    shared_vars.exectime_ranking = timer.interval
                else:
                    # do regular rank if no previous query session id was specified
                    do_regular_rank = True

            else:
                # unrecognised ranking type
                raise ValueError('Unrecognised value for rf_rank_type parameter')

            if do_regular_rank:
                # regular ranking
                print ('Computing ranking for Query ID: %d' % query_id)
                shared_vars.state = States.ranking
                with timing.TimerBlock() as timer:
                    ses.rank(query_id)
                shared_vars.exectime_ranking = timer.interval

            # mark results as ready
            shared_vars.state = States.results_ready
        except Exception as e:
            # determine if on cache exclude list
            excl_query = self.result_cache[query['engine']].query_in_exclude_list(query, ses_id=user_ses_id)
            # do the clean up below only if the query is not in the excluded list, to avoid removing previous valid results by mistake
            if not excl_query:
                # clear cache before leaving the method
                self.compdata_cache.delete_compdata(query)
                self.result_cache[query['engine']].delete_results(query, for_all_datasets=True)
            # logging
            print ('Unexpected error occurred while processing Query ID %d: %s' % (query_id, str(e)))
            traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2], limit=2)
            shared_vars.state = States.fatal_error_or_socket_timeout
            shared_vars.err_msg = str(e)
            print (traceback.format_exc())
            raise e


    def release_query_id_and_return_results(self, engine, query_id):
        """
            Instructs the backend to return the results of the query
            and then to release the query ID.
            Arguments:
                engine: backend engine to contact
                query_id: ID of the query
            Results:
                A List with all the results.
                It raises a ResultReadError if the results cannot be read.
        """
        backend_port = self.visor_opts.engines_dict[engine]['backend_port']
        ses = backend_client.Session(backend_port)

        # get ranking from backend
        rlist = ses.get_ranking(query_id)

        # Get all query results (as above) or just a subset.
        # Note that the number of results can also be restricted
        # in the backend. This last option seems better as it can
        # be adjusted PER engine
        #rsubset = ses.get_ranking_subset(query_id, 0, 5000)
        #rlist = rsubset[0]

        # release query id in backend
        ses.release_query_id(query_id)

        # check if something went wrong
        if isinstance(rlist, bool) and not rlist:
            raise errors.ResultReadError('Could not read in results from backend')

        return rlist


    def _save_classifier(self, query, fname, query_id):
        """
            Instructs the backend to save the classifier
            for the query.
            Arguments:
                query: query in dictionary form.
                query_id: id of the query.
                fname: Full path to the classifier file.
            Results:
                It raises a ClassifierSaveLoadError in case of error.
        """
        backend_port = self.visor_opts.engines_dict[query['engine']]['backend_port']
        ses = backend_client.Session(backend_port)
        if not ses.save_classifier(query_id, fname):
            raise errors.ClassifierSaveLoadError('Could not save classifier from %s' % fname)


    def _load_classifier(self, query, fname, query_id):
        """
            Instructs the backend to load the classifier
            for the query.
            Arguments:
                query: query in dictionary form.
                query_id: id of the query.
                fname: Full path to the classifier file.
            Results:
                True on success.
                It raises a ClassifierSaveLoadError in case of error.
        """
        if not os.path.isfile(fname):
            return False
        backend_port = self.visor_opts.engines_dict[query['engine']]['backend_port']
        ses = backend_client.Session(backend_port)
        if not ses.load_classifier(query_id, fname):
            raise errors.ClassifierSaveLoadError('Could not load classifier from %s' % fname)
        return True


    def _save_annotations(self, query, fname, query_id):
        """
            Instructs the backend to save the annotations
            of a query.
            Arguments:
                query: query in dictionary form.
                query_id: id of the query.
                fname: Full path to the annotations file.
            Results:
                It raises a AnnoSaveLoadError in case of error.
        """
        backend_port = self.visor_opts.engines_dict[query['engine']]['backend_port']
        ses = backend_client.Session(backend_port)
        if not ses.save_annotations(query_id, fname):
            raise errors.AnnoSaveLoadError('Could not save annotations to %s' % fname)


    def _load_annotations_and_trs(self, query, fname, query_id=None):
        """
            Instructs the backend to load the annotations
            of a query.
            Arguments:
                query: query in dictionary form.
                query_id: id of the query.
                fname: Full path to the annotations file.
            Results:
               True on success, False otherwise.
        """
        if not os.path.isfile(fname):
            return False
        backend_port = self.visor_opts.engines_dict[query['engine']]['backend_port']
        ses = backend_client.Session(backend_port)
        loaded = ses.load_annotations_and_trs(query_id, fname)
        #if not loaded:
        #    raise errors.AnnoSaveLoadError('Could not get annotations from %s' % fname)
        return loaded


    def _get_annotations(self, query, fname, query_id=None):
        """
            Retrieved the annotations of a query from the backend.
            Arguments:
                query: query in dictionary form.
                query_id: id of the query.
                fname: Full path to the annotations file.
            Results:
                On success, it returns a list of dictionaries with the
                annotations and paths to the training images.
                It raises a AnnoSaveLoadError in case of error.
        """
        if not os.path.isfile(fname):
            return []
        backend_port = self.visor_opts.engines_dict[query['engine']]['backend_port']
        ses = backend_client.Session(backend_port)
        annos = ses.get_annotations(query_id, fname)
        if not annos:
            raise errors.AnnoSaveLoadError('Could not get annotations from %s' % fname)
        return annos
