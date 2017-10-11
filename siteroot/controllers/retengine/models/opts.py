#!/usr/bin/env python

# ----------------------------------
## Enums
# ----------------------------------

class states:
    """ Enum for identifying the different states of a query """
    processing = 0
    training = 51
    ranking = 52
    results_ready = 100
    fatal_error_or_socket_timeout = 800
    invalid_qid = 850
    result_read_error = 870
    inactive = 890


class qtypes:
    """ Enum for identifying the different query types """
    text = 'text'
    curated = 'curated'
    image = 'image'
    dsetimage = 'dsetimage'
    refine = 'refine'


class rf_rank_types:
    """ Enum for identifying the different relevance feedback rank types supported """
    full = 'full'
    topn = 'topn'


class rf_train_types:
    """ Enum for identifying the different relevance feedback train types - currently not supported """
    regular = 'regular'
    augment = 'augment'


class feat_detector_type:
    """ Enum for identifying the different types of feature detectors supported """
    fast = 'fast'
    accurate = 'accurate'


class vmode:
    """ Enum of the supported view modes in the frontend """
    grid = 'grid'
    rois = 'rois'
