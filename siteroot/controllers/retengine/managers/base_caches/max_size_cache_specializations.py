#!/usr/bin/env python

from retengine import query_translations
from max_size_cache import MaxSizeCache

# ----------------------------------
## Session Cache for Results
# ----------------------------------

class MaxSizeResultCache(object):
    """ Result cache class for max-size memory cache """

    def __init__(self, entry_limit=100):
        """
            Initializes the cache.
            Arguments:
                entry_limit: maximum number of entries on the cache.
                             The default is 100 entries.
        """
        self._max_size_cache = MaxSizeCache(entry_limit)


    def get_results(self, query):
        """
            Retrieves the cached results of a query.
            Arguments:
                query: query in dictionary form.
            Returns:
                the cached list of results.
        """
        qhash = query_translations.get_qhash(query)
        return self._max_size_cache.get_data((qhash, query['qtype'], query['engine'], query['dsetname']))


    def add_results(self, rlist, query):
        """
            Stores the results of a query into the cache.
            Arguments:
                query: query in dictionary form.
                rlist: the list of results.
        """
        qhash = query_translations.get_qhash(query)
        self._max_size_cache.add_data(rlist, (qhash, query['qtype'], query['engine'], query['dsetname']))


    def delete_results(self, query, for_all_datasets=False):
        """
            Deletes the data associated with the specified query.
            Arguments:
                query: query in dictionary form.
                for_all_datasets: Boolean indicating whether to delete the results for
                                  all datasets.
        """
        qhash = query_translations.get_qhash(query)
        if not for_all_datasets:
            self._max_size_cache.delete_data((qhash, query['qtype'], query['engine'], query['dsetname']))
        else:
            self._max_size_cache.delete_data_partial_tuple((qhash, query['qtype'], query['engine'],))


    def clear_cache(self):
        """ Clears up the entire cache """
        self._max_size_cache.clear_cache()

