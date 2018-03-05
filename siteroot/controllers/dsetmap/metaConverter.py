#!/usr/bin/env python

import csv
import os
import multiprocessing
import sys

class fnameToMetaConverter:
    """
        Class for extracting metadata related to a filename.
        For a file with a filename "fname", this class expects a CSV file
        containing metadata for "fname", within the metadata_dir specified
        during the initialization of this class. Only one CSV file within
        metadata_dir will be read.
    """

    class MetaType:
        """
            Enum for the types of metadata to be extracted.
                ALLMETA: All recovered metadata for a specified file
                DESC_ONLY: Only a short description, which is defined manually below.
        """
        ALL_META=1,
        DESC_ONLY=2


    def __init__(self, prep_dsets, metadata_dir, process_pool):
        """
            Initializes the class and sets the list of supported datasets.
            Arguments:
                metadata_dir: Directory where to look for the metadata files.
                prep_dsets: Dictionary of supported datasets. The keys of this
                            dictionary are used to find the subfolder within
                            metadata_dir where the metadata of each dataset
                            should be stored.
                process_pool: instance of CpProcessPool, used to support multi-threading
        """
        self.fname2meta = {}
        self.metadata_dir = metadata_dir
        self.process_pool = process_pool
        for (dset, pretty) in prep_dsets.iteritems():
            self.fname2meta[dset] = {}
            try:
                self.process_pool.apply_async(  func=self.loadAllDsetMetadata, args=(dset, ) )
            except Exception as e:
                print "Error while pre-loading metadata for " + dset + ": " + str(e) + '\n'


    def loadAllDsetMetadata(self, dsetname):
        """
            Loads into memory the metadata of a dataset
            Arguments:
                dsetname: Key corresponding to the dataset within the list of supported
                          datasets.
        """
        for afile in os.listdir( os.path.join(self.metadata_dir, dsetname) ):
            if afile.endswith(".csv"):
                metadata_file = os.path.join(self.metadata_dir, dsetname, afile)
                with open(metadata_file, 'rb') as fin:
                    reader = csv.DictReader(fin)
                    for row in reader:
                        r_copy = dict(row)
                        del r_copy['id']
                        self.fname2meta[dsetname][row['id']] = r_copy
                        metadata = self.fname2meta[dsetname][row['id']]
                    print 'Finished loading metadata for', dsetname
            break


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
        (fpath, shorter_fname) = os.path.split(fname)

        # 1- Check dataset exists. Return just a shorter filename if it does not.
        if dsetname not in self.fname2meta.keys():
            return shorter_fname

        # 2- Check if we already loaded the metadata for this file
        metadata = None
        try:
            metadata = self.fname2meta[dsetname][fname]
        except KeyError:
            metadata = None
            pass

        # 3- If there is no metadata loaded, try to get just the information about fname
        if metadata == None:
            try:
                for afile in os.listdir( os.path.join(self.metadata_dir, dsetname) ):
                    if afile.endswith(".csv"):
                        metadata_file = os.path.join(self.metadata_dir, dsetname, afile)
                        with open(metadata_file, 'r') as fin:
                            reader = csv.DictReader(fin)
                            for row in reader:
                                if row['id'] == fname:
                                    r_copy = dict(row)
                                    del r_copy['id']
                                    self.fname2meta[dsetname][row['id']] = r_copy
                                    metadata = self.fname2meta[dsetname][row['id']]
                                    break
                        break
            except Exception as e:
                print 'metada loading exception', str(e)
                metadata = None
                pass

        # 4- If no metadata at all could be loaded, return just a shorter filename.
        if metadata == None:
            return shorter_fname

        # 5- If only the description was requested, check if the metadata contains a caption for this file
        if metadata != None and _metatype == self.MetaType.DESC_ONLY:
            if 'caption' in metadata.keys():
                return metadata['caption']
            else:
                return shorter_fname

        # 6- If all metadata was requested, return it
        if metadata != None and _metatype == self.MetaType.ALL_META:
            return metadata.items()


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





