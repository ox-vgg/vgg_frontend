#!/usr/bin/env python

import os

from retengine import models
from retengine import managers
from retengine import utils as retengine_utils
import feature_computation

# NOTE: Reverting to text query is disable for now
# from text_query import TextQuery

class CuratedQuery(object):
    """
        Class for performing curated (text) queries.

        Curated queries are the same as text queries, but the query string
        starts with the '#' character. The training images are taken from
        a subdirectory within the 'curatedtrainimgs' folder, which must be
        pre-populated with the images to be processed.
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
                The time it took to compute the features.
                It raises CuratedClassifierPathNotFoundError is the curated
                training files are not found.
        """
        try:
            imagedir = self.compdata_cache.get_image_dir(self.query)
            images = os.listdir(os.path.join(imagedir, 'positive'))
        except models.errors.CuratedClassifierPathNotFoundError as e:
            #print 'Curated classifier directory not found'
            raise e
            # NOTE: Reverting to text query is disable for now. If there are no positive images, abort !.
            #print 'Curated classifier directory not found, reverting to text search'
            #self.query['qtype'] = models.opts.Qtypes.text
            #text_query_engine = TextQuery(self.query_id, self.query, self.backend_port, self.compdata_cache, self.opts)
            #return text_query_engine.compute_feats(shared_vars)

        # get full image paths for positive images
        query_in_text_form = self.query
        query_in_text_form['qtype'] = models.opts.Qtypes.text
        featdir = self.compdata_cache.get_feature_dir(query_in_text_form)
        imgs_dict = []
        for image in images:
            (featfn, imext) = os.path.splitext(image)
            featfn += '.bin'

            # add image path to query status
            img_relative_path = imagedir[imagedir.index( os.sep + 'curatedtrainimgs'):]
            img_relative_path = os.path.join(img_relative_path, 'positive', image)
            shared_vars.curatedtrainimgs_paths = shared_vars.curatedtrainimgs_paths + [img_relative_path,]

            # create the extra_params dictionary and add anything relevant
            extra_params = dict()
            extra_params['detector'] = 'accurate' # use always the accurate detector for curated queries, if available in the backend

            # and register it for the next feature computation
            imgs_dict.append(
                {'clean_fn': os.path.join(imagedir, 'positive', image),
                 'feat_fn': os.path.join(featdir, featfn),
                 'anno': 1,
                 'from_dataset': 0,
                 'extra_params': extra_params,
                 'image' : image
                }
            )

        with retengine_utils.timing.TimerBlock() as timer:
            feat_comp = feature_computation.FeatureComputer(self.query_id, self.backend_port)
            feat_comp.compute_feats(imgs_dict)

        return timer.interval

        # NOTE: Not supporting negative images, for now.
        #
        # if not use_global_neg_trs:
        #     negimgrootdir = os.path.join(cfg['path_curatedtrainimgs'], query, 'negative')
        #     if not os.path.exists(negimgrootdir):
        #         print 'RETENGINE.ENGINE: Curated classifier negative training sample directory not found!'
        #         return False
        #     negimgpaths = os.listdir(negimgrootdir)

        #     # get full image paths for negative images
        #     negpaths = [os.path.join(negimgrootdir, image) \
        #                     for image in negimgpaths]

        #     with TimerBlock() as t:
        #         # compute features for all images in list
        #         imageproc.compfeats(negpaths,
        #                             '', query_id,
        #                             cfg['featcomp_workers'], status,
        #                             cfg['backend_port'],
        #                             cfg['log_compute_file'],
        #                             maximwidth, maximheight,
        #                             comp_neg_trs=True,
        #                             add_to_cache=True)
        #     proctime = proctime + t.interval
