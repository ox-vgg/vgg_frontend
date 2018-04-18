#!/usr/bin/env python

from threading import Lock

try:
    from collections import OrderedDict # for Python 2.7 and above
except ImportError:
    from ordereddict import OrderedDict # for Python 2.6 and below
                                        # (needs to be installed from PyPI)

# ----------------------------------
## Max Size Cache Class
# ----------------------------------

class MaxSizeCache(object):
    """
        Cache for storing generic key-value data with a limit on size

        This class stores generic key-value data in a cache with an upper limit
        on maximum size. When this limit is reached, the cache is pruned until it
        is below the size limit (configurable by the entry_limit passed on initialization).
    """

    def __init__(self, entry_limit=100):
        """
            Initializes the cache.
            Arguments:
                entry_limit: maximum number of entries on the cache.
                             The default is 100 entries.
        """
        self._datastore_lock = Lock()
        self._datastore = OrderedDict()
        self._entry_limit = entry_limit


    def __getstate__(self):
        """
            Returns a picklable object with class information for
            reconstructing the instance.
        """
        # avoid attempting to pickle unpickleable lock when serializing
        a_dict = dict(self.__dict__)
        del a_dict['_datastore_lock']
        return a_dict


    def __setstate__(self, a_dict):
        """
            Reconfigures the instance from the object specified in the parameter.
        """
        # in the deserialized output, the lock object is created anew
        self.__dict__.update(a_dict)
        self._datastore_lock = Lock()


    def purge_old_data(self, lock=True):
        """
            Clears all data which are above the storage limit.
            Arguments:
                lock: Boolean indicating whether to use a lock
                      to guarantee exclusive access to the cache before
                      purging the data.
        """
        try:
            if lock:
                self._datastore_lock.acquire()
            while len(self._datastore) > self._entry_limit:
                print 'entry count is: %d vs entry limit of : %d' % (len(self._datastore), self._entry_limit)
                self._datastore.popitem(False)
        finally:
            if lock:
                self._datastore_lock.release()


    def delete_data(self, key):
        """
            Deletes the data associated with the specified key.
            Arguments:
                key: ID of data to be deleted
        """
        with self._datastore_lock:
            if key in self._datastore:
                del self._datastore[key]


    def delete_data_partial_tuple(self, partial_tuple):
        """
            Deletes the specified tuple from the cache. Note the
            tuple is deleted from all entries.
            Arguments:
                partial_tuple: tuple to be searched and deleted from the
                               cache.
        """
        with self._datastore_lock:
            self._datastore = OrderedDict((key, ritem)
                                          for (key, ritem) in self._datastore.iteritems()
                                          if not partial_tuple == key[:len(partial_tuple)])


    def clear_cache(self):
        """ Clears up the entire cache """
        with self._datastore_lock:
            self._datastore = OrderedDict()


    def get_data(self, key):
        """
            Retrieves the data associated with the specified key.
            Arguments:
                key: ID of data to be retrieved.
            Returns:
                Data associated to the key, or 'None' if the key
                is not found in the cache.
        """
        data = None
        with self._datastore_lock:
            if key in self._datastore:
                # reinsert to update ordering
                data = self._datastore[key]
                del self._datastore[key]
                self._datastore[key] = data

        return data


    def add_data(self, data, key):
        """
            Adds data to the cache and associates it with the specified key.
            If necessary, purges old data to make room for the new entry.
            Arguments:
                key: ID of data to be stored.
                data: Data to be stored in the cache
        """
        with self._datastore_lock:
            if key in self._datastore:
                del self._datastore[key]
            self._datastore[key] = data

            self.purge_old_data(False)
