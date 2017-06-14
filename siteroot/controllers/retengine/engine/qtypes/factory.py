import engines
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
            The created object corresponding to the query type.
    """
    if query['qtype'] == models.opts.qtypes.text:
        if query['qdef'][0] == '#':
            # query['qdef'] =  query['qdef'][1:] # Remove the first special character. NOTE: Not necessary now. Disabled until needed.
            query['qtype'] = models.opts.qtypes.curated
            return engines.CuratedQuery(query_id, query,
                                        backend_port, compdata_cache, opts)
        else:
            return engines.TextQuery(query_id, query, backend_port, compdata_cache, opts)
    elif query['qtype'] == models.opts.qtypes.image:
        return engines.ImageQuery(query_id, query, backend_port, compdata_cache, opts)
    elif query['qtype'] == models.opts.qtypes.dsetimage:
        return engines.DsetimageQuery(query_id, query, backend_port, compdata_cache, opts)
    elif query['qtype'] == models.opts.qtypes.refine:
        return engines.RefineQuery(query_id, query, backend_port, compdata_cache, opts)

