from retengine.engine.qtypes.engines import dsetimage_query
from retengine.engine.qtypes.engines import image_query
from retengine.engine.qtypes.engines import text_query
from retengine.engine.qtypes.engines import refine_query
from retengine.engine.qtypes.engines import curated_query
from retengine import models

def get_query_handler(query, query_id, backend_port, compdata_cache, opts):
    """
        Main router for queries. It creates a specific object depending on the query type and
        returns it.
        Arguments:
            query: query  in dictionary form.
            query_id: id of the query.
            backend_port: Communication port with the selected backend
            compdata_cache: Computational data cache manager.
            opts: current configuration of options for the visor engine
        Returns:
            The created object corresponding to the query type, or None
            if the query type does not exists
    """
    if query['qtype'] == models.opts.Qtypes.text:
        if query['qdef'][0] == '#':
            # query['qdef'] =  query['qdef'][1:] # Remove the first special character. NOTE: Not necessary now. Disabled until needed.
            query['qtype'] = models.opts.Qtypes.curated
            return curated_query.CuratedQuery(query_id, query,
                                        backend_port, compdata_cache, opts)

        return text_query.TextQuery(query_id, query, backend_port, compdata_cache, opts)
    elif query['qtype'] == models.opts.Qtypes.image:
        return image_query.ImageQuery(query_id, query, backend_port, compdata_cache, opts)
    elif query['qtype'] == models.opts.Qtypes.dsetimage:
        return dsetimage_query.DsetimageQuery(query_id, query, backend_port, compdata_cache, opts)
    elif query['qtype'] == models.opts.Qtypes.refine:
        return refine_query.RefineQuery(query_id, query, backend_port, compdata_cache, opts)

    return None
