#!/usr/bin/env python

# ----------------------------------
## Enums
# ----------------------------------

class States:
    """ Enum for identifying the different states of a query """
    processing = 0
    training = 51
    ranking = 52
    results_ready = 100
    fatal_error_or_socket_timeout = 800
    invalid_qid = 850
    result_read_error = 870
    inactive = 890


class Qtypes:
    """ Enum for identifying the different query types """
    text = 'text'
    curated = 'curated'
    image = 'image'
    dsetimage = 'dsetimage'
    refine = 'refine'


class RfRankTypes:
    """ Enum for identifying the different relevance feedback rank types supported """
    full = 'full'
    topn = 'topn'


class RfTrainTypes:
    """
      Enum for identifying the different relevance feedback train types
      Currently not supported
    """
    regular = 'regular'
    augment = 'augment'


class FeatDetectorType:
    """ Enum for identifying the different types of feature detectors supported """
    fast = 'fast'
    accurate = 'accurate'


class Vmode:
    """ Enum of the supported view modes in the frontend """
    grid = 'grid'
    rois = 'rois'
