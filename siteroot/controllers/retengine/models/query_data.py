#!/usr/bin/env python

import opts

# ----------------------------------
## Query data structures
# ----------------------------------

class QueryStatus(object):
    """ Class for storing the status of a query at a given time """

    def __init__(self, qid=None, query=None,
                 state=opts.States.inactive,
                 postrainimg_paths=[], curatedtrainimgs_paths=[], negtrainimg_count=0,
                 exectime_processing=0.0, exectime_training=0.0,
                 exectime_ranking=0.0, err_msg=''):
        """
            Initializes the class
            Arguments:
                 qid: query id
                 query: query in dictionary form
                 state: initial state of the query
                 postrainimg_paths: Paths to the positive training images
                 curatedtrainimgs_paths: Paths to the images for curated training
                 negtrainimg_count: Counter of negative training images
                 exectime_processing: Execution time spent on processing
                 exectime_training: Execution time spent on training
                 exectime_ranking: Execution time spent on ranking
                 err_msg: Message indicating the cause of an error with the query.
        """
        self.qid = qid
        self.query = query
        self.state = state
        self.postrainimg_paths = postrainimg_paths
        self.curatedtrainimgs_paths = curatedtrainimgs_paths
        self.negtrainimg_count = negtrainimg_count
        self.exectime_processing = exectime_processing
        self.exectime_training = exectime_training
        self.exectime_ranking = exectime_ranking
        self.err_msg = err_msg


    def to_dict(self):
        """
            Converts the attributes to a dictionary
            Returns:
                The status in dictionary form
        """
        return dict((k, v) for (k, v) in self.__dict__.iteritems() if not k.startswith('__'))


class QueryData(object):
    """
        Class for storing the data associated to a query, i.e., its
        status and the list of results associated with it.
    """

    def __init__(self, status=QueryStatus(), rlist=None):
        """
            Initializes the class
            Arguments:
                 status: Initial query status
                 rlist: Initial list of results
        """
        if not isinstance(status, QueryStatus):
            raise ValueError('status must be of type QueryStatus')
        self.status = status
        self.rlist = rlist


    def to_dict(self):
        """
            Converts the attributes to a dictionary. Only two keys are
            used: 'status' will contain the current status of the query
            and 'rlist' will contain the current list of query results.
            Returns:
                The query data in dictionary form.
        """
        return {'status': self.status.to_dict(),
                'rlist': self.rlist}
