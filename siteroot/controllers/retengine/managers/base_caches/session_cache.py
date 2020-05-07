#!/usr/bin/env python

from time import time
from threading import Lock

# ----------------------------------
## Session Cache Class
# ----------------------------------

class SessionCache(object):
    """
        Cache for storing generic key-value data for a time-limited session

        This class stores data in a two level dictionary, with the first level being
        a unique ID intended to be associated with a 'session' and the second level being
        the data index itself. When reading/writing data, both the session ID and regular
        index are required. Any data associated with a 'session' which has not been
        read or written to recently will be periodically removed (configurable by the
        session_lifetime argument passed on initialization).
    """

    class SessionData(object):
        """ Class for storing generic data for a single session """
        def __init__(self):
            self.last_update = time()
            self.data = {}


    def __init__(self, session_lifetime=1200):
        """
            Initializes the cache.
            Arguments:
                session_lifetime: number of seconds before a cache entry
                                  expires. The default is 20 minutes.
        """
        self._sessions_lock = Lock()
        self._sessions = dict()
        self._session_lifetime = session_lifetime


    def __getstate__(self):
        """
            Returns a picklable object with class information for
            reconstructing the instance.
        """
        # avoid attempting to pickle unpickleable lock when serializing
        a_dict = dict(self.__dict__)
        del a_dict['_sessions_lock']
        return a_dict


    def __setstate__(self, a_dict):
        """
            Reconfigures the instance from the object specified in the parameter.
        """
        # in the deserialized output, the lock object is created anew
        self.__dict__.update(a_dict)
        self._sessions_lock = Lock()


    def purge_old_sessions(self, lock=True):
        """
            Clears all sessions which haven't been accessed recently.
            Arguments:
                lock: Boolean indicating whether to use a lock
                      to guarantee exclusive access to the cache before
                      purging the data.
        """
        try:
            if lock:
                self._sessions_lock.acquire()
            for key in self._sessions.keys():
                if (time() - self._sessions[key].last_update) > self._session_lifetime:
                    del self._sessions[key]
        finally:
            if lock:
                self._sessions_lock.release()


    def delete_session(self, ses_id):
        """
            Deletes the data associated with the specified session.
            Arguments:
                ses_id: ID of the session
        """
        with self._sessions_lock:
            if ses_id in self._sessions:
                del self._sessions[ses_id]

            self.purge_old_sessions(False)


    def delete_data(self, ses_id, key):
        """
            Deletes the data associated with the specified key within a
            session.
            Arguments:
                key: ID of data to be deleted within the session
                ses_id: ID of the session
        """
        with self._sessions_lock:
            if ses_id in self._sessions:
                if key in self._sessions[ses_id].data:
                    del self._sessions[ses_id].data[key]

            self.purge_old_sessions(False)


    def delete_data_partial_tuple(self, ses_id, partial_tuple):
        """
            Deletes the specified tuple from the specified session. Note the
            tuple is deleted from all entries in the session.
            Arguments:
                ses_id: ID of the session
                partial_tuple: tuple to be searched and deleted
        """
        with self._sessions_lock:
            if ses_id in self._sessions:
                self._sessions[ses_id] = dict((key, item)
                                              for (key, item)
                                              in self._sessions[ses_id].items()
                                              if not partial_tuple == key[:len(partial_tuple)])


    def get_data(self, ses_id, key=None):
        """
            Retrieves the data associated with a session and a key.
            Arguments:
                ses_id: ID of the session
                key: ID of data to be retrieved within the session.
            Returns:
                Data associated to the key, or 'None' if the key
                is not found in the session.
        """
        data = None
        with self._sessions_lock:
            if ses_id in self._sessions:
                self._sessions[ses_id].last_update = time()
                if key:
                    if key in self._sessions[ses_id].data:
                        data = self._sessions[ses_id].data[key]
                else:
                    data = self._sessions[ses_id].data

            self.purge_old_sessions(False)

        return data


    def delete_data_unknown_session(self, data, key):
        """
            Searches for a data value associated with a key within all sessions
            and deletes each session where an exact match is found
            If necessary, purges old data to make room for new entries.
            Arguments:
                data: data value to search
                key: ID associated to the data to be searched.
        """
        with self._sessions_lock:
            found_ses = []
            for ses_id in self._sessions:
                if key and key in self._sessions[ses_id].data:
                    for (key_, item) in self._sessions[ses_id].data[key].items():
                        if data == item:
                            found_ses.append(ses_id)
            for ses_id in found_ses:
                del self._sessions[ses_id]

            self.purge_old_sessions(False)


    def add_data(self, data, ses_id, key):
        """
            Adds data to a session and associates it with the specified key.
            If necessary, purges old data to make room for the new entry.
            Arguments:
                ses_id: ID of the session
                key: ID of data to be stored.
                data: Data to be stored in the cache
        """
        with self._sessions_lock:
            if ses_id not in self._sessions:
                self._sessions[ses_id] = self.SessionData()
            self._sessions[ses_id].last_update = time()
            self._sessions[ses_id].data[key] = data

            self.purge_old_sessions(False)


    def clear_all_sessions(self):
        """ Clears up the entire cache """
        self._sessions = dict()
