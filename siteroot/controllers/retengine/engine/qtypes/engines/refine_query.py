#!/usr/bin/env python

from base_query import BaseQuery

class RefineQuery(BaseQuery):
    """
        Class for performing for refining a previous image query.

        Given that the results from other query types are always lists
        of images, this kind of query operates similar to an image query,
        but the source directory can vary depending on the query being
        refined.
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
        """
        self.from_dataset = False
        self.srv_imgdir = 'postrainimgs/%s/' % query['engine']
        self.featdir = compdata_cache.get_feature_dir(query)
        self.imagedir = compdata_cache.get_image_dir(query)
        # if the refinement comes from a curated search, redirect to curatedtrainimgs folder
        if 'curated__' in str(query['qdef']):
            self.srv_imgdir = 'curatedtrainimgs/%s/' % query['engine']

        super(RefineQuery, self).__init__(query_id, query, backend_port,
                                          compdata_cache, opts)
