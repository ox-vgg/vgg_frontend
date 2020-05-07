#!/usr/bin/env python

import os
from copy import deepcopy

from retengine import models
from retengine.managers import compdata_cache as compdata_cache_module
from retengine.utils import timing
from . import feature_computation


class BaseQuery(object):
    """
        Base class for all (non-text) query handlers

        The following member variables should be set by derived classes:
            featdir
            imagedir
            srv_imgdir
            from_dataset
    """

    def __init__(self, query_id, query, backend_port, compdata_cache, opts):
        """
            Initializes the query object.
            Arguments:
                query: query  in dictionary form.
                query_id: id of the query.
                backend_port: Communication port with the selected backend
                compdata_cache: Computational data cache manager.
                opts: current configuration of options for the visor engine
            Returns:
                It raises ValueError in case of incorrect options or
                computational cache
        """
        if not isinstance(opts, models.param_sets.VisorEngineProcessOpts):
            raise ValueError('opts must be of type models.param_sets.VisorEngineProcessOpts')
        if not isinstance(compdata_cache, compdata_cache_module.CompDataCache):
            raise ValueError('compdata_cache must be of type compdata_cache.CompDataCache')

        self.query_id = query_id
        self.query = query
        self.backend_port = backend_port
        self.compdata_cache = compdata_cache
        self.opts = opts
        #the following 3 variables should be set by the derived class
        #self.featdir
        #self.imagedir
        #self.srv_imgdir


    def compute_feats(self, shared_vars=None):
        """
            Performs the computation of features.
            It prepares input data and then invokes FeatureComputer with it.
            Arguments:
                shared_vars: holder of global shared variables
            Returns:
                The time it took to compute the features
        """
        image_dict = deepcopy(self.query['qdef'])
        for image in image_dict:
            imfn = image['image'].replace(self.srv_imgdir, '')
            imfn = imfn.replace('%23', '#') # replace html-encoded curated search character
            del image['image']
            (featfn, imext) = os.path.splitext(imfn)
            featfn += '.bin'
            image['clean_fn'] = os.path.join(self.imagedir, imfn)
            image['feat_fn'] = os.path.join(self.featdir, featfn)

            # from_dataset is always required, so add this to top level of dict
            image['from_dataset'] = self.from_dataset

            # ensure there is an extra_params node
            if not 'extra_params' in image:
                image['extra_params'] = {}

            # use the detector selected in the options
            image['extra_params']['detector'] = self.opts.feat_detector_type

            # move anno to outside of extra_params dict, as it is always required
            # when computing features (and also convert it to an integer)
            if 'anno' in image['extra_params']:
                image['anno'] = int(image['extra_params']['anno'])
                del image['extra_params']['anno']
            else:
                image['anno'] = 1

        with timing.TimerBlock() as timer:
            feat_comp = feature_computation.FeatureComputer(self.query_id, self.backend_port)
            feat_comp.compute_feats(image_dict)

        return timer.interval
