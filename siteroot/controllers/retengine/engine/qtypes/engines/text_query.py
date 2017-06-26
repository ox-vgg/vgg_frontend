#!/usr/bin/env python

import os
import sys
import threading
import requests
import zmq
import random
try:
    import simplejson as json
except ImportError:
    import json  # Python 2.6+ only

from retengine import models
from retengine import managers
from retengine import utils as retengine_utils

random.seed()
ZMQ_IMPATH_TERMINATE_MSG = 'TERMINATE'
POSTRAINIMGS_DIRNAME = 'postrainimgs'

class TextQuery(object):
    """
        Class for performing text queries.

        This query invokes the imsearchtool to download training images
        from the web, by using the query string as input to an image
        search engine.

        If a particular text engine does not support images as input,
        the downloading step can be skipped by configuring the engine
        with its 'imgtools_postproc_module' set to 'None'.
    """

    def __init__(self, query_id, query, backend_port, compdata_cache, opts):
        """
            Initializes the class.
            Arguments:
                query_id: id of the query being executed.
                query: query in dictionary form
                backend_port: Communication port with the backend
                compdata_cache: Computational data cache manager.
                opts: current configuration of options for the visor engine
            Returns:
                It raises ValueError in case of incorrect options or
                computational cache
        """
        if not isinstance(opts, models.param_sets.VisorEngineProcessOpts):
            raise ValueError('opts must be of type models.param_sets.VisorEngineProcessOpts')
        if not isinstance(compdata_cache, managers.CompDataCache):
            raise ValueError('compdata_cache must be of type managers.CompDataCache')

        self.query_id = query_id
        self.query = query
        self.backend_port = backend_port
        self.compdata_cache = compdata_cache
        self.opts = opts


    def compute_feats(self, shared_vars):
        """
            Performs the computation of features.
            Arguments:
                shared_vars: holder of global shared variables
            Returns:
                The time it took to download the trainig images and process them.
                If the 'imgtools_postproc_module' of the search engine is set to
                'None', it will return zero.
        """
        # Check that a imgtools_postproc_module has actually been configured ...
        if self.compdata_cache.engines_dict[ self.query['engine'] ]['imgtools_postproc_module'] != None:

            # get output image directory from compdata_cache
            imagedir = self.compdata_cache.get_image_dir(self.query)
            featdir = self.compdata_cache.get_feature_dir(self.query)

            # Clear out some previous images
            self.compdata_cache.cleanup_unused_query_postrainimgs_cache(self.query)

            # call imsearchtool service
            pipe_name_hash = str(int(round(random.random()*1000000.0)))
            zmq_impath_return_ch = 'ipc:///tmp/zmq_url_return_ch_' + pipe_name_hash
            return self._call_imsearchtool(imagedir, featdir, zmq_impath_return_ch, shared_vars)

        else:

            # ... and do not download images otherwise
            return 0

    def _call_imsearchtool(self, imagedir, featdir, zmq_impath_return_ch=None,
                           shared_vars=None):
        """
            Calls the imsearchtool service to download positive training images and send them
            to the backend for processing.
            Arguments:
                imagedir: path to the folder where the downloaded images will be stored
                featdir: path to the folder where the computed features will be stored
                zmq_impath_return_ch: ZMQ return channel
                shared_vars: holder of global shared variables
            Returns:
                The time it took to download the training images and process them.
                It raises ValueError if zmq_impath_return_ch is specified but not shared_vars, as the latter is
                used to start the thread to read the ZMQ socket.
        """
        # validate parameters
        if zmq_impath_return_ch and not shared_vars:
            raise ValueError("'shared_vars' parameter must be passed if passing a ZMQ return channel in 'zmq_impath_return_ch'")

        # spawn thread to receive impath callback if required
        if zmq_impath_return_ch:
            istreceiver = IstImpathReturnThread(zmq_impath_return_ch, shared_vars)
            istreceiver.start()

        # make HTTP request
        # print 'Query ID for current query: %d' % self.query_id
        with retengine_utils.timing.TimerBlock() as t:
            try:
                # preinitialize zmq socket
                func_loc = ('http://%s:%d/init_zmq_context' % \
                            (self.opts.imsearchtools_opts['service_host'],
                             self.opts.imsearchtools_opts['service_port']))
                r = requests.get(func_loc)
                func_loc = ('http://%s:%d/exec_pipeline' % \
                            (self.opts.imsearchtools_opts['service_host'],
                             self.opts.imsearchtools_opts['service_port']))
                extra_prms = {'func': 'addPosTrs',
                              'backend_host': 'localhost',
                              'backend_port': self.backend_port,
                              'query_id': self.query_id,
                              'featdir': featdir,
                              }

                if zmq_impath_return_ch:
                    extra_prms['zmq_impath_return_ch'] = zmq_impath_return_ch
                request_data = {'q': self.query['qdef'],
                                'postproc_module': self.compdata_cache.engines_dict[ self.query['engine'] ]['imgtools_postproc_module'],
                                'postproc_extra_prms': json.dumps(extra_prms),
                                'engine': self.opts.imsearchtools_opts['engine'],
                                'custom_local_path': imagedir,
                                'query_timeout': self.opts.imsearchtools_opts['query_timeout'],
                                'improc_timeout': self.opts.imsearchtools_opts['improc_timeout'],
                                'per_image_timeout': self.opts.imsearchtools_opts['per_image_timeout'],
                                'num_results': self.opts.imsearchtools_opts['num_pos_train'],
                                'resize_width': self.opts.resize_width,
                                'resize_height': self.opts.resize_height,
                                'style': self.compdata_cache.engines_dict[ self.query['engine'] ]['imgtools_style']}
                r = requests.post(func_loc,
                                  data=request_data,
                                  timeout=10*60) #times out at 10m
            except requests.exceptions.Timeout:
                print 'Image download and feature computation timed out for query:', self.query
            except requests.exceptions.ConnectionError, e:
                print 'Could not connect to imsearchtool service'
                raise e

        comp_time = t.interval
        # print 'Done with call to imsearchtool for Query ID:', self.query_id

        # send terminate message to impath callback thread if required
        if zmq_impath_return_ch:
            istreceiver_terminator = istreceiver.context.socket(zmq.REQ)
            istreceiver_terminator.connect(zmq_impath_return_ch)
            istreceiver_terminator.send(ZMQ_IMPATH_TERMINATE_MSG)
            istreceiver_terminator.recv()
            # wait max of 50ms for join just in case
            istreceiver.join(0.050)
        #print 'Done with call to imsearchtool for Query ID:', self.query_id

        return comp_time


class IstImpathReturnThread(threading.Thread):
    """
        Class implementing the thread which download images from the
        image search provider.
    """

    def __init__(self, impath_return_ch, shared_vars):
        """
            Initializes the class
            Arguments:
                impath_return_ch: ZMQ return channel
                shared_vars: holder of global shared variables
        """
        self.shared_vars = shared_vars
        # prepare ZMQ socket to receive image paths as they are processed
        self.context = zmq.Context()
        self.impath_receiver = self.context.socket(zmq.REP)
        self.impath_receiver.bind(impath_return_ch)
        os.chmod(impath_return_ch[6:], 0774)
        print 'done initialization'

        super(IstImpathReturnThread, self).__init__()


    def run(self):
        """
            Executes the thread.
            Stores the paths to the downloaded training images in the
            holder of global shared variables.
        """
        try:
            while True:
                print 'receiving'
                zmq_msg = self.impath_receiver.recv()
                print 'received'
                # break on receiving terminate message
                if zmq_msg == ZMQ_IMPATH_TERMINATE_MSG:
                    self.impath_receiver.send('RECEIVED')
                    break
                # otherwise message is image path, so append it to postrainimg_paths
                diridx = zmq_msg.find(POSTRAINIMGS_DIRNAME)
                if diridx < 1:
                    raise runtime_error('Could not parse path to positive training \
                                         image path - check POSTRAINIMGS_DIRNAME \
                                         variable')
                zmq_msg = zmq_msg[diridx-1:]
                self.shared_vars.postrainimg_paths = self.shared_vars.postrainimg_paths + [zmq_msg,]
                # print 'Updated postrainimg_paths:', zmq_msg
                self.impath_receiver.send('RECEIVED')
        finally:
            print 'received terminate message'
            #self.impath_receiver.close()
            #self.context.term()
