#!/usr/bin/env python

from base_query import BaseQuery

class ImageQuery(BaseQuery):
    """
        Class for performing an image query using images uploaded by the user
        or downloaded from an image search provider.
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
        self.featdir = compdata_cache.get_feature_dir(query)
        self.imagedir = compdata_cache.get_image_dir(query)
        self.srv_imgdir = '/uploadedimgs/'
        super(ImageQuery, self).__init__(query_id, query, backend_port,
                                         compdata_cache, opts)
