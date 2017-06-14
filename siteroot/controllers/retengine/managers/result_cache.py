#!/usr/bin/env python

import msgpack
import os
import re
import string

from retengine import utils
from retengine import models
import base_caches

#
# Cache Inheritance Hierarchy:
#
#       ---------------             ---------------
#      | MaxSizeCache |            | SessionCache |- - - - - - - - - - - -
#      ---------------             ---------------                       :
#             :                         :                                :
#   ---------[]----------       -------[]-----------------       -------[]------------
#  | MaxSizeResultCache |- -   | SessionExcludeListCache |    - | SessionResultCache |
#  ---------------------   :   --------------------------    :  ---------------------
#                          - - - - - -   |      - - - - - - -
#                                    :   v     :
#                                  -[]--------[]-
#                                 | ResultCache |
#                                 --------------
#
#      mem cache provided by MaxSizeResultCache
#          (stores results in memory indefinitely, up to last 100 results)
#      query_ses cache provided by SessionResultCache
#          (stores results only for lifetime of query + 15 mins)
#      disk cache managed directly
#          (stores results on disk indefinitely)
#
#      SessionExcludeListCache is used to cache excluded queries on the basis of
#      which the cache to use is determined

# can contain query_strid
PATTERN_FNAME_RESULTS = '${dsetname}___${query_strid}.msgpack'

class ResultCache(base_caches.SessionExcludeListCache):
    """
        Cache for results in VISOR frontend (interfaces to both memory and disk cache)

        All saving/loading of results can operate through three possible cache systems:

          memory cache        - stores last N results to memory
          disk cache          - stores unlimited results to disk
          query session cache - stores result to memory over short-term (~15 mins)
                                  accessible only to callers specifying the same
                                  query session ID

        One or more active caches can be specified for the case that caching is enabled
        and disabled. By default, the configuration is:

          caching enabled     - use memory + disk cache
          caching disabled    - use query session cache only
    """

    # ----------------------------------
    ## Enums for storing cache options
    # ----------------------------------

    class Caches(object):
        """ Enum for identifying the different types of caches """
        disk = 'disk'
        mem = 'mem'
        query_ses = 'query_ses'


    class CacheCfg(object):
        """ Enum for identifying the different types of cache configuration """
        all = ['disk', 'mem']
        disk_only = ['disk']
        mem_only = ['mem']
        query_ses_only = ['query_ses']
        none = []

    # ----------------------------------
    ## Start of main class implementation
    # ----------------------------------

    def __init__(self, ranklistpath, process_pool, enabled_caches=CacheCfg.all,
                 enabled_excl_caches=CacheCfg.none):
        """
            Initializes the cache.
            Arguments:
                ranklistpath: Path to folder with ranking lists
                process_pool: pool of workers for multi-threading processing
                enabled_caches: caches to use in normal operation.
                                It should be a valid CacheCfg value.
                enabled_excl_caches: caches to use for queries on exclude list.
                                     It should be a valid CacheCfg value.
        """
        self.ranklistpath = ranklistpath
        # process pool for saving ranking lists in background
        self.process_pool = process_pool

        self.enabled_caches = enabled_caches
        self.enabled_excl_caches = enabled_excl_caches

        self._mem_cache = base_caches.MaxSizeResultCache(entry_limit=5)
        self._query_ses_cache = base_caches.SessionResultCache()

        # following cache used to store query_ses_id -> query obj lookup
        self._query_ses_id_cache = base_caches.MaxSizeCache()

        self._bg_worker = None

        super(ResultCache, self).__init__()


    def __getstate__(self):
        """
            Returns a picklable object with class information for
            reconstructing the instance.
        """
        # avoid attempting to pickle unpickleable worker pools when serializing
        d = dict(self.__dict__)
        del d['process_pool']
        return d


    def __setstate__(self, d):
        """
            Reconfigures the instance from the object specified in the parameter.
        """
        # in the deserialized output, process_pool is set to None
        self.__dict__.update(d)
        self.process_pool = None


    def get_all_disk_cached_text_querystrs(self, return_empty_list_if_cache_enabled=False):
        """
            Gets a list of all queries in the disk cache as query objects.
            ONLY qtype TEXT is supported (as other types are hashed).
            Arguments:
                return_empty_list_if_cache_enabled: Set to True to return an
                            empty list when the cache is enabled.
            Returns:
                A list of queries, regardless of whether the disk cache is
                enabled or not by default. This behaviour can be changed using
                'return_empty_list_if_cache_enabled'.
        """
        querystrs = []

        if (not return_empty_list_if_cache_enabled or
            self.Caches.disk in self.enabled_caches):
            if os.path.exists(self.ranklistpath):
                rankfiles = os.listdir(self.ranklistpath)
                for rankfile in rankfiles:
                    rankfile, rankfileext = os.path.splitext(rankfile)
                    dsetname, strid = rankfile.split('___', 2)

                    try:
                        querystr, qtype = utils.tag_utils.decode_query_strid(strid)
                    except models.errors.StrIdDecodeError:
                        continue

                    querystrs.append(querystr)

        return querystrs


    def get_results(self, query, query_ses_id=None, user_ses_id=None):
        """
            Gets results (from disk, memory or query session cache) for a query
            or return 'None' if the query does not exist in the cache.
            Arguments:
                query: query in dictionary form.
                query_ses_id: ID associated to the query in this cache.
                user_ses_id: User session ID.
            Returns:
                The list of results associated to the query in the cache.
        """
        # determine if on cache exclude list
        excl_query = self.query_in_exclude_list(query, ses_id=user_ses_id)

        rlist = None
        # print '-------------------------------'
        # print 'query_ses_id: %s' % query_ses_id
        # print 'user_ses_id: %s' % user_ses_id
        # print 'query: %s (%s)' % (query['qdef'], query['dsetname'])
        # print 'enabled caches: %s' % ctxt_enabled_caches
        # print 'query on exclude list: %s' % excl_query
        # print '-------------------------------'

        # read from cache if possible ----------
        ctxt_enabled_caches = self.enabled_caches if not excl_query else self.enabled_excl_caches
        if self.Caches.mem in ctxt_enabled_caches:
            # check memory cache first
            # print 'Memory cache enabled - checking for results...'
            rlist = self._mem_cache.get_results(query)
            # print 'Retrieved from memory cache: %s' % (rlist is not None)
        if not rlist and self.Caches.disk in ctxt_enabled_caches:
            # otherwise try loading from disk
            # print ''Disk cache enabled - checking for results...'
            rlist = self._load_results_from_disk(query)
            # print 'Retrieved from disk cache: %s' % (rlist is not None)
            # ...and add to memory cache while we're at it
            if self.Caches.mem in ctxt_enabled_caches and rlist:
                self._mem_cache.add_results(rlist, query)
            # ...and add to session cache while we're at it
            if self.Caches.query_ses in ctxt_enabled_caches and rlist:
                self._query_ses_cache.add_results(rlist, query_ses_id, query)
        elif self.Caches.query_ses in ctxt_enabled_caches and query_ses_id:
            # print 'Query session cache enabled - checking for results...'
            rlist = self._query_ses_cache.get_results(query_ses_id, query)
            # print 'Retrieved from query session cache: %s' % (rlist is not None)

        # finally, add query object to query session id cache
        # if it is not there already
        if query_ses_id:
            if not self._query_ses_id_cache.get_data(query_ses_id):
                # print 'Added query_ses_id lookup: %s' % query_ses_id
                self._query_ses_id_cache.add_data(query, query_ses_id)

        return rlist


    def get_results_from_query_ses_id(self, query_ses_id, user_ses_id=None):
        """
            Gets results associated to the given query_ses_id from the
            query session cache.
            NOTE: the cache exclude list is ignored for this function.
            Arguments:
                query_ses_id: ID associated to the query in this cache.
                user_ses_id: User session ID.
            Returns:
                The list of results associated to the query in the cache
                IF it is enabled. It returns 'None' if the cache is
                disabled or the query_ses_id does not exist.
        """
        ctxt_enabled_caches = self.enabled_caches
        # print 'Checking for results by query_ses_id: %s...' % query_ses_id

        # try to get query object from query_ses_id
        query = self._query_ses_id_cache.get_data(query_ses_id)
        if not query:
            print 'Failed to find result using query_ses_id: %s - returning None' % query_ses_id
            return None

        return self.get_results(query, query_ses_id, user_ses_id)
        # print 'Retrieved by query_ses_id: %s' % (rlist is not None)

        return rlist


    def add_results(self, rlist, query,
                    query_ses_id=None, user_ses_id=None):
        """
            Adds a set of results to the query cache (both memory + disk).
            Arguments:
                rlist: List of results associated to the query.
                query: query in dictionary form.
                query_ses_id: ID associated to the query in this cache.
                user_ses_id: User session ID.
        """
        # determine if on cache exclude list
        excl_query = self.query_in_exclude_list(query, ses_id=user_ses_id)

        ctxt_enabled_caches = self.enabled_caches if not excl_query \
            else self.enabled_excl_caches

        if self.Caches.mem in ctxt_enabled_caches:
            # save to memory cache first
            self._mem_cache.add_results(rlist, query)
        if self.Caches.disk in ctxt_enabled_caches:
            # finally, save result to disk cache in background
            self.process_pool.apply_async(func=self._save_results_to_disk,
                                          args=(query,))
        if self.Caches.query_ses in ctxt_enabled_caches and query_ses_id:
            # also save to query session cache if required
            self._query_ses_cache.add_results(rlist, query_ses_id, query)

        # finally, add query object to query session id cache
        if query_ses_id:
            # print 'Added query_ses_id lookup: %s' % query_ses_id
            self._query_ses_id_cache.add_data(query, query_ses_id)


    def delete_results(self, query, for_all_datasets=False, caches=CacheCfg.all,
                       query_ses_id=None):
        """
            Deletes results from cache (both memory + disk unless otherwise specified)
            if dsetname is not specified, the query specified is deleted for
            ALL datasets.
            Arguments:
                query: query in dictionary form.
                for_all_datasets: Boolean indicating whether to delete the results for
                                  all datasets.
                caches: a CacheCfg enum value
                query_ses_id: ID associated to the query in this cache.
        """
        # remove from memory cache
        if self.Caches.mem in caches:
            self._mem_cache.delete_results(query, for_all_datasets)

        # remove from disk cache
        if self.Caches.disk in caches:
            if for_all_datasets:
                fname_regex = self._get_disk_fname(query)
                fname_regex = fname_regex.replace(query['dsetname'], '(.+)')
                # uber classifiers contain $ on the name and that breaks
                # the regular expression search in the code below
                fname_regex = fname_regex.replace('$','\$')

                a_dir = os.path.dirname(fname_regex)
                a_files = os.listdir(a_dir)

                all_fnames = [os.path.join(a_dir, a_file) for a_file in a_files]
                # just get fnames which conform to regular expression
                fnames = [fname for fname in all_fnames if re.search(fname_regex, fname)]

                for fname in fnames:
                    if os.path.isfile(fname):
                        os.remove(fname)
                        print 'REMOVED FILE: ' + fname
            else:
                fname = self._get_disk_fname(query)
                if os.path.isfile(fname):
                    # print 'Removed ranking file from disk: %s' % fname
                    os.remove(fname)

        # remove from query session cache
        if self.Caches.query_ses in caches and query_ses_id:
            self._query_ses_cache.delete_results(query_ses_id, query)

    # ----------------------------------
    ## Clear caches
    # ----------------------------------

    def clear_all_caches(self):
        """ Clears up all caches """
        # clear memory cache
        self._mem_cache.clear_cache()
        # clear session caches
        self.clear_all_sessions()
        self._query_ses_cache.clear_all_sessions()
        # clear disk cache
        utils.fileutils.delete_directory_contents(self.ranklistpath)

    # ----------------------------------
    ## Get paths and disk filenames
    # ----------------------------------

    def _get_disk_fname(self, query):
        """
            Gets the full path and filename of the ranking file associated
            to the query.
            Arguments:
                query: query in dictionary form.
            Returns:
                A file path where the file name follows PATTERN_FNAME_RESULTS.
        """
        query_strid = utils.tag_utils.get_query_strid(query)
        fname_template = string.Template(PATTERN_FNAME_RESULTS)
        fname = fname_template.substitute(query_strid=query_strid,
                                          dsetname=query['dsetname'])
        try:
            os.makedirs(self.ranklistpath)
        except OSError:
            pass

        return os.path.join(self.ranklistpath, fname)


    def _load_results_from_disk(self, query):
        """
            Loads from a local ranking list file the results associated
            to the specified query.
            Arguments:
                query: query in dictionary form.
            Returns:
                The list of results associated to the query, or 'None' if
                it was not possible to read the file.
        """
        fname = self._get_disk_fname(query)
        if os.path.isfile(fname):
            try:
                with open(fname, 'rb') as rfile:
                    rlist = msgpack.load(rfile)
            except:
                return None
            return rlist
        else:
            return None


    def _save_results_to_disk(self, query):
        """
            Saves the results of a query to a local ranking list file.
            Arguments:
                query: query in dictionary form.
        """
        fname = self._get_disk_fname(query)
        rlist = self._mem_cache.get_results(query)

        with open(fname, 'wb') as rfile:
            msgpack.dump(rlist, rfile)
