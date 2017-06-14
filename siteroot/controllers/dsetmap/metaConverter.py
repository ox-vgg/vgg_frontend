#!/usr/bin/env python

import csv
import os.path
try:
    import simplejson as json
except ImportError:
    import json  # Python 2.6+ only

# logging
import logging
log = logging.getLogger(__name__)


class MetaloadError(Exception):
    """ Class for reporting errors related to the metadata conversion """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class fnameToMetaConverter:
    """
        Class for extracting metadata related to a filename.
        For a file with a filename "fname", this class expects a JSON file
        containing metadata for "fname", within the metadata_dir specified
        during the initialization of this class. The path to the JSON file
        is derived from the path to "fname".
    """

    class MetaType:
        """
            Enum for the types of metadata to be extracted.
                ALLMETA: All recovered metadata for a specified file
                DESC_ONLY: Only a short description, which is defined manually below.
        """
        ALL_META=1,
        DESC_ONLY=2


    def __init__(self, prep_dsets, metadata_dir):
        """
            Initializes the class and sets the list of supported datasets.
            Arguments:
                metadata_dir: Directory where to look for the metadata files.
                prep_dsets: Dictionary of supported datasets. The keys of this
                            dictionary are used to find the subfolder within
                            metadata_dir where the metadata of each dataset
                            should be stored.
        """
        self.fname2meta = {}
        self.metadata_dir = metadata_dir
        for (dset, pretty) in prep_dsets.iteritems():
            self.fname2meta[dset] = {}

    def getMetaFromFname(self, fname, dsetname, _metatype=MetaType.ALL_META):
        """
            Extracts the metadata corresponding to the specified file, within
            the specified dataset.
            Arguments:
                fname:  Full path to the file for which the metadata is being
                        extracted
                dsetname: Key corresponding to the dataset within the list of supported
                          datasets.
                _metatype: Type of metadata to be extracted. Must be a value
                           of class MetaType
            Returns:
                A string with the extracted metadata, possibly in JSON format.
        """

        # get filename basename
        # (which will be returned if nothing more meaningful can be found)
        (fpath, fname) = os.path.split(fname)

        if fpath:
            if fpath[0] == '/': fpath = fpath[1:]

        # if the dataset is not supported, just return fname
        if dsetname not in self.fname2meta.keys():
            return fname

        metadata = None

        try:
            # Check if we already loaded the metadata for this ...
            metadata = self.fname2meta[dsetname][fname]
        except KeyError:
            metadata = None
            pass

        # ... if we didn't, load the provided metadata file
        if metadata == None:
            metadata_file = os.path.join(self.metadata_dir, dsetname, 'metadata.csv')
            try:
                with open(metadata_file, 'rb') as f:
                    reader = csv.reader(f)
                    self.fname2meta[dsetname] = { row[0]: row[1:] for row in reader}
                    metadata = self.fname2meta[dsetname][fname]
            except Exception as e:
                print e
                metadata = None
                pass

        # ... if we couldn't load the provided metadata file
        if metadata == None:
            return fname
        else:
            if _metatype == self.MetaType.DESC_ONLY:
                return metadata[0]
            else:
                return metadata


    def getDescFromFname(self, fname, dsetname):
        """
            Extracts a short description corresponding to the specified file, within
            the specified dataset.
            Arguments:
                fname:  Full path to the file for which the description is being
                        extracted.
                dsetname: Key corresponding to the dataset within the list of supported
                          datasets.
            Returns:
                A string with the extracted description, possibly in JSON format.
        """
        return self.getMetaFromFname(fname, dsetname, _metatype=self.MetaType.DESC_ONLY)


    def getSupportedDatasets(self):
        """ Returns the list of supported datasets """
        return self.fname2meta.keys()





