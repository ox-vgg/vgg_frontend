import os
import sys

from retengine.engine import backend_client
from retengine import utils as retengine_utils
from retengine import models


class FeatureComputer(object):
    """ Contacts the backend to perform features computation """

    def __init__(self, query_id, backend_port):
        """
            Initializes the class.
            Arguments:
                query_id: id of the query being executed.
                backend_port: Communication port with the backend
        """
        self.query_id = query_id
        self.backend_port = backend_port


    def compute_feats(self, out_dicts):
        """
            Performs the computation of features for a set of files.
            Arguments:
                out_dicts: List of dictionaries where each entry contains
                           information about the file to process, the annotations
                           for the file and where to store the computed features.
            Returns:
                The time it took to compute the features
        """
        with retengine_utils.timing.TimerBlock() as t:
            out_dicts = [dict(self.__dict__.items() + out_dict.items())
                         for out_dict in out_dicts]
            map(_compute_feat, out_dicts)

        comp_time = t.interval
        ##print 'Done with call to compute_feats for Query ID:', self.query_id
        return comp_time


def _compute_feat(out_dict):
    """
        Performs the computation of features for one file.
        Arguments:
            out_dicts: Dictionary with at least the following entries:
                       'clean_fn': Path to input file for processing.
                       'feat_fn': Path to file where features are stored.
                       'backend_port': Communication port with the backend
                       'anno': 1 if the image is a positive training image, -1
                               if it is a negative training image, 0 otherwise.
                       'query_id': id of the query being executed.
                       'from_dataset': Boolean indicating whether the training image
                                       is part of the dataset or not.
                       'extra_params': Dictionary containing any other parameter that
                                       can be useful to the backend.
        Returns:
            It raises FeatureCompError is the backend reports something went
            wrong with the feature computation.
    """
    impath = out_dict['clean_fn']
    featpath = out_dict['feat_fn']

    ses = backend_client.Session(out_dict['backend_port'])

    is_symlink = os.path.islink(impath)
    if is_symlink:
        canonical_impath = os.path.realpath(impath)
    else:
        canonical_impath = impath

    is_symlink_feat = os.path.islink(featpath)
    if is_symlink_feat:
        canonical_featpath = os.path.realpath(featpath)
    else:
        canonical_featpath = featpath

    if out_dict['anno'] == 1:
        call_succeeded = ses.add_pos_trs(out_dict['query_id'],
                                         canonical_impath, canonical_featpath,
                                         out_dict['from_dataset'],
                                         out_dict['extra_params'])
    elif out_dict['anno'] == -1:
        call_succeeded = ses.add_neg_trs(out_dict['query_id'],
                                         canonical_impath, canonical_featpath,
                                         out_dict['from_dataset'],
                                         out_dict['extra_params'])
    else:
        call_succeeded = True

    if call_succeeded == False:
        raise models.errors.FeatureCompError('Failed computing features of ' + canonical_impath)

    if is_symlink:
        sys.stdout.write('computed features for: ' + impath +
                         ' (=>' + canonical_impath + ')\n')
    else:
        sys.stdout.write('computed features for: ' + impath + '\n')

    ##print "Backend call done: ", impath


