#!/usr/bin/env python

# ----------------------------------
## Errors
# ----------------------------------

class ResultReadError(Exception):
    """ Class for reporting errors related to reading results from the backend """
    def __init__(self, msg):
        super(ResultReadError, self).__init__()
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class QueryIdError(Exception):
    """ Class for reporting errors related to reading results from the backend """
    def __init__(self, msg):
        super(QueryIdError, self).__init__()
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class CuratedClassifierPathNotFoundError(Exception):
    """ Class for reporting errors when the training images folder of a curated query is not found """
    def __init__(self, msg):
        super(CuratedClassifierPathNotFoundError, self).__init__()
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class UnsupportedQtypeError(Exception):
    """ Class for reporting errors when the attempting to use a query type that is not supported """
    def __init__(self, msg):
        super(UnsupportedQtypeError, self).__init__()
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class FeatureCompError(Exception):
    """ Class for reporting errors related to feature computations """
    def __init__(self, msg):
        super(FeatureCompError, self).__init__()
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class VisorBackendUnreachableError(Exception):
    """ Class for reporting errors when a backend is unreachable """
    def __init__(self, msg):
        super(VisorBackendUnreachableError, self).__init__()
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class AnnoSaveLoadError(Exception):
    """ Class for reporting errors when the annotations of a classifier cannot be loaded or saved """
    def __init__(self, msg):
        super(AnnoSaveLoadError, self).__init__()
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class ClassifierTrainError(Exception):
    """ Class for reporting errors when there is an error during the training of a classifier """
    def __init__(self, msg):
        super(ClassifierTrainError, self).__init__()
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class ClassifierSaveLoadError(Exception):
    """ Class for reporting errors when a classifier cannot be loaded or saved """
    def __init__(self, msg):
        super(ClassifierSaveLoadError, self).__init__()
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class StrIdDecodeError(Exception):
    """ Class for reporting errors related to decoding a string id """
    def __init__(self, msg):
        super(StrIdDecodeError, self).__init__()
        self.msg = msg

    def __str__(self):
        return repr(self.msg)
