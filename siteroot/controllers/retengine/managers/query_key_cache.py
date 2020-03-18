#!/usr/bin/env python

from hashlib import md5
from time import time as unix_time

from retengine.managers.base_caches import session_cache

#
# Cache Inheritance Hierarchy:
#
#            ---------------
#           | SessionCache |
#           ---------------
#                :
#           ----[]----------
#          | QueryKeyCache |
#          ----------------

class QueryKeyCache(object):
    """
        Query cache for storing on-going query definition dictionaries by query session id.
        Interfaces to transient memory cache.
        It uses an internal SessionCache object to store the keys.
    """

    def __init__(self, session_lifetime=900):
        """
            Initializes the cache.
            Arguments:
                session_lifetime: number of seconds before a cache entry
                                  expires. The default is 15 minutes.
        """
        self._session_cache = session_cache.SessionCache(session_lifetime)


    def delete_text_query_unknown_session(self, query_text):
        """
            Searches for all sessions matching the query_text and removes
            them from the cache.
            Arguments:
                query_text: query text
        """
        self._session_cache.delete_data_unknown_session(query_text, "query")


    def gen_query_session_id(self, query):
        """
            Generates a query key ID and stores the query
            in the cache associating it with the generated ID.
            Arguments:
                query: query in dictionary form.
            Returns:
                The generated ID.
        """
        query_ses_id = md5( str(unix_time()).encode('utf-8') ).hexdigest()

        self._session_cache.add_data(query, query_ses_id, "query")
        self._session_cache.add_data(None, query_ses_id, "backend_qid")
        #print ('Generated qsid: %s with query: %s' % (query_ses_id, query['qdef']))
        return query_ses_id


    def set_query_session_backend_qid(self, qid, query_ses_id):
        """
            Stores the backend ID of a query.
            Arguments:
                qid: ID of the query in the backend.
                query_ses_id: ID associated to the query in this cache.
        """
        self._session_cache.add_data(qid, query_ses_id, "backend_qid")
        #if qid is not None:
            #print ('Set qid of qsid: %s to: %d' % (query_ses_id, qid))
        #else:
            #print ('Set qid of qsid: %s to: None' % query_ses_id)


    def get_query_details_and_qid(self, query_ses_id):
        """
            Retrieves the data stored in the cache, associated to the
            specified ID.
            Arguments:
                query_ses_id: ID associated to the query in this cache.
            Returns:
                A tuple with two elements. The first one corresponds to
                a query dictionary and the second to the ID of the query
                in the backend.
        """
        query = self._session_cache.get_data(query_ses_id, "query")
        qid = self._session_cache.get_data(query_ses_id, "backend_qid")
        #print ('Lookup of qsid: %s gave query: %s' % (query_ses_id, query))
        return (query, qid)


    def get_query_details(self, query_ses_id):
        """
            Retrieves the query dictionary associated to the specified ID.
            Arguments:
                query_ses_id: ID associated to the query in this cache.
            Returns:
                A query dictionary.
        """
        return self.get_query_details_and_qid(query_ses_id)[0]


    def delete_query_session(self, query_ses_id):
        """
            Removes the data associated to the specified ID from the cache.
            Arguments:
                query_ses_id: ID associated to the query in this cache.
        """
        self._session_cache.delete_session(query_ses_id)
        #print ('Deleted qsid data: %s' % query_ses_id)


    def clear_all_sessions(self):
        """ Clears up the entire cache """
        self._session_cache.clear_all_sessions()
