#!/usr/bin/env python

import csv
import os
import time
import json
import shutil

from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, KEYWORD, TEXT
from whoosh.qparser import QueryParser
from whoosh.collectors import TimeLimitCollector, TimeLimit
from whoosh.writing import AsyncWriter

class MetaDataHandler:
    """
        Class handling all operations related to a dataset's metadata.
        For each dataset, this class expects a CSV file containing metadata
        within the metadata_dir specified during the initialization of this
        class. Only one CSV file within metadata_dir will be read.
    """

    class MetaType:
        """
            Enum for the types of metadata to be extracted.
                ALLMETA: All recovered metadata for a specified file
                DESC_ONLY: Only a short description, which is defined manually below.
        """
        ALL_META = 1,
        DESC_ONLY = 2


    def __init__(self, prep_dsets, metadata_dir, process_pool, keywords_wildcard='*'):
        """
            Initializes the class and sets the list of supported datasets.
            Arguments:
                metadata_dir: Directory where to look for the metadata files.
                prep_dsets: Dictionary of supported datasets. The keys of this
                            dictionary are used to find the subfolder within
                            metadata_dir where the metadata of each dataset
                            should be stored.
                process_pool: instance of CpProcessPool, used to support multi-threading
                keywords_wildcard: wildcard character for keyword-based search. It should be JUST ONE CHARACTER and cannot be '#'.
        """
        self.fname2meta = {}
        self.keyword2fname = {}
        self.metadata_dir = metadata_dir
        self.process_pool = process_pool
        self.keywords_wildcard = keywords_wildcard
        # load metadata for each dataset
        self.metaindex = None
        self.is_all_metadata_loaded = False
        found_a_csv = False
        for (dset, pretty) in prep_dsets.items():
            self.fname2meta[dset] = {}
            self.keyword2fname[dset] = {}
            try:
                # check there is at least one csv
                if not found_a_csv:
                    for afile in os.listdir(os.path.join(self.metadata_dir, dset)):
                        if afile.endswith(".csv"):
                            found_a_csv = True
                            break
                # create index, if not present
                self.index_dir = os.path.join(self.metadata_dir, 'indexdir')
                create_index = False
                if found_a_csv and not os.path.exists(self.index_dir):
                    os.mkdir(self.index_dir)
                    schema = Schema(key=KEYWORD(stored=True),
                                    dataset=TEXT) # In the future, this migth be needed if
                                                  # using multiple datasets
                    self.metaindex = create_in(self.index_dir, schema)
                    create_index = True
                # load the old one, if found
                if found_a_csv and os.path.exists(self.index_dir):
                    self.metaindex = open_dir(self.index_dir)
                # start thread to load all metadata
                self.process_pool.apply_async(func=self.load_all_dset_metadata, args=(dset, create_index,))
            except Exception as e:
                print ("Error while pre-loading metadata for " + dset + ": " + str(e) + '\n')


    def load_all_dset_metadata(self, dsetname, create_index=False):
        """
            Loads into memory the metadata of a dataset. The metadata is read from a CSV file, which should
            have at least two columns:
             - filename: Paths to the images in the dataset, relative to the image data folder. For backward
                         compatibility '#filename' is also accepted
             - file_attributes: JSON string containing information about the file. The most important file
                                attributes are 'caption' and 'keywords'. The 'caption' field should be a short
                                string which will be used as the caption of the image in result lists. The
                                'keywords' field must contain a comma-separated list of keywords. Each keyword
                                can be used as the source for a search.
            If create_index is True, it builds a search index with the 'keywords' in the file_attributes.
            Arguments:
                dsetname: String corresponding to the dataset within the list of supported
                          datasets.
                create_index: Boolean indicating whether or not to build a search index
                              with the metadata
        """
        metaindex = None
        t = time.time()
        try:
            for afile in os.listdir(os.path.join(self.metadata_dir, dsetname)):
                if afile.endswith(".csv"):
                    metadata_file = os.path.join(self.metadata_dir, dsetname, afile)
                    print ('Found metadata file at', metadata_file)
                    if create_index:
                        metaindex = open_dir(self.index_dir)
                    with open(metadata_file, 'r') as fin:
                        reader = csv.DictReader(fin)
                        for row in reader:
                            id_field = None
                            if 'filename' in row.keys():
                                id_field = 'filename'
                            elif '#filename' in row.keys():
                                id_field = '#filename'
                            if id_field and 'file_attributes' in row.keys():
                                filename = row[id_field]
                                try:
                                    self.fname2meta[dsetname][filename] = json.loads(row['file_attributes'])
                                except:
                                    self.fname2meta[dsetname][filename] = None
                                metadata = self.fname2meta[dsetname][filename]
                                keyword_list = None
                                if metadata and 'keywords' in metadata.keys():
                                    keyword_list = metadata['keywords']
                                if keyword_list and create_index:
                                    keyword_list_splitted = keyword_list.split(',')
                                    writer = AsyncWriter(metaindex)
                                    for key in keyword_list_splitted:
                                        key = key.strip()
                                        # delete previous entry if found
                                        query = QueryParser('key', metaindex.schema).parse(key)
                                        writer.delete_by_query(query, metaindex.searcher())
                                        # add document
                                        writer.add_document(key=str(key), dataset=str(dsetname))
                                    writer.commit()
                                if keyword_list: # we would like to do this, even if the index is not created
                                    # register link keyword-file
                                    keyword_list_splitted = keyword_list.split(',')
                                    for key in keyword_list_splitted:
                                        key = key.strip()
                                        if key in self.keyword2fname[dsetname].keys():
                                            self.keyword2fname[dsetname][key].append(filename)
                                        else:
                                            self.keyword2fname[dsetname][key] = [filename]
                            else:
                                raise Exception('"filename" and/or "file_attributes" columns not found in ' + afile + ' (are you missing the column names?). Metadata will not be available!.')

                        print ('Finished loading metadata for %s in %s' % (dsetname, str(time.time()-t)))
                        self.is_all_metadata_loaded = True
                    break
        except Exception as e:
            print ("load_all_dset_metadata Exception:" + str(e) + '\n')


    def get_files_by_keyword(self, keyword, dsetname):
        """
            Returns the list of files associated to a keyword in the metadata index
            Arguments:
                keyword: text from the 'key' field in the metadata index
                dsetname: string corresponding to the dataset within the list of supported
                          datasets.
            Returns:
                A list of path to files, relatives to the image data folder
        """
        results_list = []
        try:
            if keyword == self.keywords_wildcard:
                for key in self.keyword2fname[dsetname].keys():
                    results_list.extend(self.keyword2fname[dsetname][key])
            else:
                results_list = self.keyword2fname[dsetname][keyword]
        except Exception as e:
            print (e)
            results_list = []

        return results_list


    def search_metaindex_by_keyword(self, text, limit=None, timelimit=1):
        """
            Performs a query in the metadata search index by the 'key' field.
            Arguments:
                text: String used to perform the search in the index.
                limit: Maximum number of results to be returned. By default there is no limit.
                timelimit: Maximum number of seconds to execute the search. Searches that
                           take longer than timelimit will return only partial results.
            Returns:
                A list of dictionaries, each containing the fields in the metadata
                index, whose values match the query text in the 'key' field.
        """
        results_list = []
        if self.metaindex:
            with self.metaindex.searcher() as searcher:
                query = QueryParser('key', self.metaindex.schema).parse(text)
                coll = searcher.collector(limit)
                tlc = TimeLimitCollector(coll, timelimit, use_alarm=False)

                # Try searching
                try:
                    searcher.search_with_collector(query, tlc)
                except TimeLimit:
                    print ("searchByKeyWord: Index search took too long, aborting!")

                # get partial results, if available
                results = tlc.results()
                for res in results:
                    results_list.append(dict(res))

        return results_list


    def get_search_suggestions(self, text):
        """
            Gathers a list of maximum 100 search suggestions from the metadata search index.
            The timeout for a search in the index is 0.5 seconds. Searches that
            take longer will return only partial results.
            Arguments:
                text: String used to perform the search in the index
            Returns:
                A list of maximum 100 suggestions
        """
        suggestions = [ self.keywords_wildcard ]
        results = self.search_metaindex_by_keyword(text + '*', limit=100, timelimit=0.5)
        for res in results:
            suggestions.append(res['key'])
        return suggestions


    def get_meta_from_fname(self, fname, dsetname, _metatype=MetaType.ALL_META):
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

        # 3- If no metadata was found, return just a shorter filename, otherwise keep going
        if metadata == None:
            return shorter_fname

        # 4- If only the description was requested, check if the metadata contains a caption for this file
        if metadata != None and _metatype == self.MetaType.DESC_ONLY:
            if 'caption' in metadata.keys():
                return metadata['caption']
            else:
                return shorter_fname

        # 5- If all metadata was requested, return it
        if metadata != None and _metatype == self.MetaType.ALL_META:
            return metadata.items()


    def get_desc_from_fname(self, fname, dsetname):
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
        return self.get_meta_from_fname(fname, dsetname, _metatype=self.MetaType.DESC_ONLY)


    def get_supported_datasets(self):
        """ Returns the list of supported datasets """
        return self.fname2meta.keys()


    def clear_metadata_index(self):
        """
            Clears the metadata index by removing the index directory
        """
        try:
            shutil.rmtree(self.index_dir)
            self.is_all_metadata_loaded = False
        except Exception as e:
            print ('clear_metadata_index Exception: ' + str(e))
            pass
