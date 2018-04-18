#!/usr/bin/env python

from retengine import query_translations
from session_cache import SessionCache


# ----------------------------------
## Session Cache for Query Exclude List
# ----------------------------------

class SessionExcludeListCache(object):
    """ Exclude list session cache class """

    def __init__(self, session_lifetime=1800):
        """
            Initializes the cache.
            Arguments:
                session_lifetime: number of seconds before a cache entry
                                  expires. The default is 30 minutes.
        """
        self.cache_exclude_list = set([])
        # initialize session cache with expiry time of 30 mins
        self._session_cache = SessionCache(session_lifetime)


    def query_in_exclude_list(self, query, ses_id=None):
        """
            Searches for a query in the query exclude list.
            Arguments:
                query: query in dictionary form.
                ses_id: ID of the session.
            Returns:
                True if the query is found in the list, False otherwise.
        """
        # if no session ID specified, allow storage under a 'universal' tag
        if not ses_id:
            ses_id = 'universal'
        qhash = query_translations.get_qhash(query, include_engine=True, include_qtype=True)
        # get the data itself
        data = self._session_cache.get_data(ses_id, qhash)
        # print 'Looking for query in exclude list: (%s), ses_id: %s, class: %s - %s' %
        #       (qhash, ses_id, self.__class__.__name__, data != None)
        # return only whether the key was present or not (and had non-None data)
        return data != None


    def add_query_to_exclude_list(self, query, ses_id=None):
        """
            Adds a query to the query exclude list.
            Arguments:
                query: query in dictionary form.
                ses_id: ID of the session.
        """
        # if no session ID specified, allow storage under a 'universal' tag
        if not ses_id:
            ses_id = 'universal'
        qhash = query_translations.get_qhash(query, include_engine=True, include_qtype=True)
        # print 'Adding query to exclude list: (%s), ses_id: %s, class: %s' %
        #       (qhash, ses_id, self.__class__.__name__)
        # add dummy data as only the keys of excluded queries are important
        self._session_cache.add_data('excluded query', ses_id, qhash)


    def clear_query_exclude_list(self, ses_id):
        """
            Clears up the query exclude list associated to a session.
            Arguments:
                ses_id: ID of the session.
        """
        # if no session ID specified, allow storage under a 'universal' tag
        if not ses_id:
            ses_id = 'universal'
        # delete session entirely to remove all query excludes
        self._session_cache.delete_session(ses_id)


    def clear_all_sessions(self):
        """ Clears up the entire cache """
        self._session_cache.clear_all_sessions()


# ----------------------------------
## Session Cache for Results
# ----------------------------------

class SessionResultCache(object):
    """ Result session cache class """

    def __init__(self, session_lifetime=900):
        """
            Initializes the cache.
            Arguments:
                session_lifetime: number of seconds before a cache entry
                                  expires. The default is 15 minutes.
        """
        self._session_cache = SessionCache(session_lifetime)


    def get_results(self, ses_id, query=None):
        """
            Gets the results of a query from a session.
            Arguments:
                query: query in dictionary form.
                ses_id: ID of the session.
            Returns:
                The list of results associated to the query.
        """
        if query:
            qhash = query_translations.get_qhash(query, include_qtype=True)
            return self._session_cache.get_data(ses_id, (qhash, query['engine'], query['dsetname']))

        # returns data dictionary directly if no query key was specified
        return self._session_cache.get_data(ses_id)


    def add_results(self, rlist, ses_id, query):
        """
            Adds the results of a query to a session cache
            Arguments:
                rlist: List of results associated to the query.
                query: query in dictionary form.
                ses_id: ID of the session.
        """
        qhash = query_translations.get_qhash(query, include_qtype=True)
        self._session_cache.add_data(rlist, ses_id, (qhash, query['engine'], query['dsetname']))


    def delete_results(self, ses_id, query, for_all_datasets=False):
        """
            Deletes the results of the specified query from a session cache.
            Arguments:
                ses_id: ID of the session cache.
                query: query in dictionary form.
                for_all_datasets: Boolean indicating whether to delete the results for
                                  all datasets.
        """
        qhash = query_translations.get_qhash(query, include_qtype=True)
        if not for_all_datasets:
            self._session_cache.delete_data(ses_id, (qhash, query['engine'], query['dsetname']))
        else:
            self._session_cache.delete_data_partial_tuple(ses_id, (qhash, query['engine'],))


    def clear_all_sessions(self):
        """ Clears up the entire cache """
        self._session_cache.clear_all_sessions()
