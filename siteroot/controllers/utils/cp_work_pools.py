#!/usr/bin/env python

import multiprocessing
from multiprocessing.pool import ThreadPool # needed for the dummy pool

class CpProcessPool:
    """
        Simple manager for a pool of worker processes.
        It uses a multiprocessing.dummy.Pool instead of a regular
        multiprocessing.Pool. The later causes I/O errors when the
        server is shutdown (or restarted). The dummy implementation
        seems to provide better performance as well.
        Members:
            _workers: the private pool of worker processes.
            processes: number of worker processes in the pool.
    """

    def __init__(self, processes=10):
        """
            Initializes the pool
            Arguments:
                processes: number of worker processes to create for the pool.
        """
        self._workers = None
        self.processes = processes


    def start(self):
        """ Starts all the processes in the pool. """
        try:
            if not self._workers:
                print 'Starting CpProcessPool...'
                self._workers = multiprocessing.dummy.Pool(processes=self.processes)
                # NOTE: Using a 'real' Pool (not a dummy Pool) causes I/O errors when the
                # server is shutdown (or restarted). The dummy implementation seems to
                # provide better performance as well.
        except Exception as e:
            print 'CpProcessPool start: ', e


    def close(self):
        """ Closes the pool. """
        try:
            if self._workers:
                print 'Closing CpProcessPool...'
                self._workers.close()
                self._workers = None
                print 'Closed CpProcessPool'
        except Exception as e:
            print 'CpProcessPool close: ', e


    def stop(self):
        """ Terminates all process in the pool. """
        try:
            if self._workers:
                print 'Stopping CpProcessPool...'
                self._workers.terminate()
                self._workers.join()
                self._workers = None
                print 'Stopped CpProcessPool'
        except Exception as e:
            print 'CpProcessPool stop: ', e


    def apply_async(self, **kwargs):
        """
            Executes the given function using the pool.
            Arguments:
                kwargs: This should be a function with its arguments.
        """
        try:
            if self._workers:
                #print 'Submitting task to CpProcessPool...'
                self._workers.apply_async(**kwargs)
        except Exception as e:
            print 'CpProcessPool apply_async: ', e
