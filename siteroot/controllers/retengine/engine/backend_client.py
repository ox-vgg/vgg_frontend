#!/usr/bin/env python

import socket
try:
    import simplejson as json
except ImportError:
    import json  # Python 2.6+ only
import urllib

TCP_TERMINATOR = "$$$"
SUCCESS_FIELD = "success"
TCP_TIMEOUT = 86400.00

class Session(object):
    """
        Low-level interface to VISOR backend.

        Implements TCP/IP client capable of interacting directly with the
        VISOR backend, and exposes wrapper functions for all methods provided
        by it.
    """

    def __init__(self, port, host="localhost", verbose=False):
        """
            Initializes the class.
            Arguments:
                port: port number in the target machine
                host: target machine host name
                verbose: set to True to print out console messages
                         (not currently used, reserved for expansion)
        """
        self.port = port
        self.host = host
        self.verbose = verbose
        self.leftovers = ''


    def prepare_success_json_str_(self, success):
        """
            Creates a JSON with ONLY a 'success' field
            Arguments:
                Parameters: Boolean value for the 'success' field
            Returns:
                JSON formatted string
        """
        retfail = {}
        retfail[SUCCESS_FIELD] = success
        return json.dumps(retfail)


    def custom_request(self, request, append_end=True):
        """
            Sends a request to the host and port specified in the creation
            of the class.
            Arguments:
                request: JSON object to be sent
                append_end: Boolean to indicate whether or not to append
                            a TCP_TERMINATOR value at the end of the request.
            Returns:
                JSON containing the response from the host
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self.host, self.port))
        except socket.error, msg:
            print 'Connect failed', msg
            return self.prepare_success_json_str_(False)

        sock.settimeout(TCP_TIMEOUT)

        print 'Request to VISOR backend at port %s: %s' % (str(self.port), request)

        if append_end:
            request += TCP_TERMINATOR

        total_sent = 0
        while total_sent < len(request):
            sent = sock.send(request[total_sent:])
            if sent == 0:
                raise RuntimeError("Socket connection broken at port " + str(self.port))
            total_sent = total_sent + sent

        term_idx = -1
        response = self.leftovers
        while term_idx < 0:
            try:
                rep_chunk = sock.recv(1024)
                if not rep_chunk:
                    print 'Connection closed! at port ' + str(self.port)
                    sock.close()
                    return self.prepare_success_json_str_(False)

                response = response + rep_chunk
                term_idx = response.find(TCP_TERMINATOR)
            except socket.timeout:
                print 'Socket timeout at port ' + str(self.port)
                sock.close()
                return self.prepare_success_json_str_(False)

        excess_sz = term_idx + len(TCP_TERMINATOR)
        self.leftovers = response[excess_sz:]

        response = response[0:term_idx]

        sock.close()
        return response


    def self_test(self):
        """
            Simple 'ping' method to check the backend is running.
            It calls 'selfTest' in the backend.
            Returns:
                True on success, False otherwise.
        """
        func_in = {}
        func_in["func"] = "selfTest"
        request = json.dumps(func_in)

        # self test should just return true in status field
        response = self.custom_request(request)

        func_out = json.loads(response)
        # return boolean true if no problems
        return func_out[SUCCESS_FIELD]


    def get_query_id(self, dataset):
        """
            Request a new query ID from the backend.
            It calls 'getQueryId' in the backend.
            Arguments:
                dataset: dataset over which the query is performed.
            Returns:
                A positive integer number corresponding to the new query ID.
        """
        func_in = {}
        func_in["func"] = "getQueryId"
        func_in["dataset"] = dataset
        request = json.dumps(func_in)

        response = self.custom_request(request)

        #TODO: when the request fails, we need to trigger a more usefull error. This applies for all requests in this file.

        func_out = json.loads(response)
        if "query_id" in func_out:
            return func_out["query_id"]

        return -1


    def release_query_id(self, query_id):
        """
            Instructs the backend to release a query ID. After this
            the backend could reuse the ID for a new query.
            It calls 'releaseQueryId' in the backend.
            Arguments:
                query_id: id to be released.
            Returns:
               True on success, False otherwise.
        """
        func_in = {}
        func_in["func"] = "releaseQueryId"
        func_in["query_id"] = query_id
        request = json.dumps(func_in)

        response = self.custom_request(request)

        func_out = json.loads(response)
        return func_out[SUCCESS_FIELD]


    def add_pos_trs(self, query_id, impath, featpath,
                    from_dataset=False, extra_params=None):
        """
            Instructs the backend to add a positive training image to a
            query.
            It calls 'addPosTrs' in the backend.
            Arguments:
                query_id: id of the query.
                impath: Full path to the training image.
                featpath: Full path to the feature file associated to the query.
                from_dataset: Boolean indicating whether the training image
                              is part of the dataset or not.
                extra_params: Dictionary containing any other parameter that
                              can be useful to the backend.
            Returns:
               True on success, False otherwise.
        """
        func_in = {}
        #TODO: Fix this later with passing it as a parameter in extra_params
        add_to_cache = False
        if add_to_cache:
            func_in["func"] = "addPosTrsAndCache"
        else:
            func_in["func"] = "addPosTrs"
        func_in["query_id"] = query_id
        func_in["impath"] = urllib.unquote(urllib.unquote(impath)) # decode possibly url-encoded image names
        func_in["featpath"] = featpath
        func_in["from_dataset"] = (1 if from_dataset else 0)

        if extra_params:
            func_in["extra_params"] = extra_params

        request = json.dumps(func_in)
        response = self.custom_request(request)

        func_out = json.loads(response)
        return func_out[SUCCESS_FIELD]


    def add_neg_trs(self, query_id, impath, featpath,
                    from_dataset=False, extra_params=None):
        """
            Instructs the backend to add a negative training image to a
            query.
            It calls 'addNegTrs' in the backend.
            Arguments:
                query_id: id of the query.
                impath: Full path to the training image.
                featpath: Full path to the feature file associated to the query.
                from_dataset: Boolean indicating whether the training image
                              is part of the dataset or not.
                extra_params: Dictionary containing any other parameter that
                              can be useful to the backend.
            Returns:
               True on success, False otherwise.
        """
        func_in = {}
        #TODO: Fix this later with passing it as a parameter in extra_params
        add_to_cache = False

        if add_to_cache:
            func_in["func"] = "addNegTrsAndCache"
        else:
            func_in["func"] = "addNegTrs"
        func_in["query_id"] = query_id
        func_in["impath"] = urllib.unquote(urllib.unquote(impath)) # decode possibly url-encoded image names
        func_in["featpath"] = featpath
        func_in["from_dataset"] = (1 if from_dataset else 0)

        if extra_params:
            func_in["extra_params"] = extra_params

        request = json.dumps(func_in)
        response = self.custom_request(request)

        func_out = json.loads(response)
        return func_out[SUCCESS_FIELD]


    def train(self, query_id, anno_path=None):
        """
            Executes the training process on the backend.
            It calls 'train' in the backend.
            Arguments:
                query_id: id of the query.
                anno_path: Full path to the annotations associated to the query.
            Returns:
               It returns 'None' on success, or an error message otherwise
        """
        func_in = {}
        func_in["func"] = "train"
        func_in["query_id"] = query_id

        if anno_path:
            func_in["anno_path"] = anno_path
        request = json.dumps(func_in)

        response = self.custom_request(request)

        func_out = json.loads(response)

        if func_out[SUCCESS_FIELD]:
            return None
        elif 'err_msg' in func_out:
            return func_out['err_msg']

        return str(func_out[SUCCESS_FIELD])


    def load_classifier(self, query_id, fname):
        """
            Instructs the backend to load a classifier file.
            It calls 'loadClassifier' in the backend.
            Arguments:
                query_id: id of the query.
                fname: Full path to the classifier file.
            Returns:
               True on success, False otherwise.
        """
        func_in = {}
        func_in["func"] = "loadClassifier"
        func_in["query_id"] = query_id
        func_in["filepath"] = fname
        request = json.dumps(func_in)

        response = self.custom_request(request)

        func_out = json.loads(response)
        return func_out[SUCCESS_FIELD]


    def save_classifier(self, query_id, fname):
        """
            Instructs the backend to save a classifier file.
            It calls 'saveClassifier' in the backend.
            Arguments:
                query_id: id of the query.
                fname: Full path to the classifier file.
            Returns:
               True on success, False otherwise.
        """
        func_in = {}
        func_in["func"] = "saveClassifier"
        func_in["query_id"] = query_id
        func_in["filepath"] = fname
        request = json.dumps(func_in)

        response = self.custom_request(request)

        func_out = json.loads(response)
        return func_out[SUCCESS_FIELD]


    def load_annotations_and_trs(self, query_id, fname):
        """
            Instructs the backend to load an annotations file.
            It should differ from 'get_annotations' in that this function
            should return a simple value indicating the success (or not) of the
            loading process.
            It calls 'loadAnnotationsAndTrs' in the backend.
            Arguments:
                query_id: id of the query.
                fname: Full path to the annotations file.
            Returns:
               True on success, False otherwise.
        """
        func_in = {}
        func_in["func"] = "loadAnnotationsAndTrs"
        func_in["query_id"] = query_id
        func_in["filepath"] = fname
        request = json.dumps(func_in)

        response = self.custom_request(request)

        func_out = json.loads(response)
        return func_out[SUCCESS_FIELD]


    def get_annotations(self, query_id, fname):
        """
            Instructs the backend to retrieve the contents
            of an annotations file.
            It should differ from 'load_annotations_and_trs' in that this function
            should return a list of dictionaries with the actual annotations.
            It calls 'getAnnotations' in the backend.
            The backend should return the results in JSON format with
            at least the field: 'annos'.
            Arguments:
                query_id: id of the query.
                fname: Full path to the annotations file.
            Returns:
                On success, it returns a list of dictionaries with the
                annotations and paths to the training images. It
                returns False otherwise.
        """
        func_in = {}
        func_in["func"] = "getAnnotations"
        func_in["query_id"] = query_id
        func_in["filepath"] = fname
        request = json.dumps(func_in)

        response = self.custom_request(request)

        func_out = json.loads(response)
        if func_out[SUCCESS_FIELD]:
            return func_out["annos"]

        return False


    def save_annotations(self, query_id, fname):
        """
            Instructs the backend to save an annotations file.
            It calls 'saveAnnotations' in the backend.
            Arguments:
                query_id: id of the query.
                fname: Full path to the annotations file.
            Returns:
               True on success, False otherwise.
        """
        func_in = {}
        func_in["func"] = "saveAnnotations"
        func_in["query_id"] = query_id
        func_in["filepath"] = fname
        request = json.dumps(func_in)

        response = self.custom_request(request)

        func_out = json.loads(response)
        return func_out[SUCCESS_FIELD]


    def rank(self, query_id, subset_ids=None):
        """
            Executes the ranking process on the backend.
            The ranking can be executed over all the results or over
            a subset of them.
            It calls 'rank' in the backend.
            Arguments:
                query_id: id of the query.
                subset_ids: List specifying the ids of items within the
                            rank, so that only those items are ranked.
            Returns:
               True on success, False otherwise.
        """
        func_in = {}
        func_in["func"] = "rank"
        func_in["query_id"] = query_id
        if subset_ids:
            func_in["subset_ids"] = subset_ids
        request = json.dumps(func_in)

        response = self.custom_request(request)

        func_out = json.loads(response)
        return func_out[SUCCESS_FIELD]


    def get_ranking(self, query_id):
        """
            Gets the ranked list of results. Ranked results
            must be arranged in ascendant order by their score.
            It calls 'getRanking' in the backend.
            The backend should return the results in JSON format with
            at least the field: 'ranklist'.
            Arguments:
                query_id: id of the query.
            Returns:
                On success, it returns a list with the paths and scores
                of the ranked results. It returns False otherwise.
        """
        func_in = {}
        func_in["func"] = "getRanking"
        func_in["query_id"] = query_id
        request = json.dumps(func_in)

        response = self.custom_request(request)

        func_out = json.loads(response)
        if func_out[SUCCESS_FIELD]:
            return func_out["ranklist"]

        return False


    def get_ranking_subset(self, query_id, start_idx, end_idx):
        """
            Gets a subset of the ranked list of results. Ranked results
            must be arranged in ascendant order by their score.
            It calls 'getRankingSubset' in the backend.
            The backend should return the results in JSON format with
            at least the fields: 'ranklist', 'total_len'.
            Arguments:
                query_id: id of the query.
                start_idx: subset start index.
                end_idx: subset end index.
            Returns:
                On success it returns a pair, where the first item corresponds
                to the list with the paths and scores of the ranked subset of
                results, and the second item is the length of the subset. It
                returns False otherwise.
        """
        func_in = {}
        func_in["func"] = "getRankingSubset"
        func_in["query_id"] = query_id
        func_in["start_idx"] = start_idx
        func_in["end_idx"] = end_idx
        request = json.dumps(func_in)

        response = self.custom_request(request)

        func_out = json.loads(response)
        if func_out[SUCCESS_FIELD]:
            return (func_out["ranklist"], func_out["total_len"])

        return False


    def get_ranked_features(self, query_id, top_n=300):
        """
            Gets the features of the ranked results.
            It calls 'getRankedFeatures' in the backend.
            The backend should return the results in JSON format with
            at least the field: 'rfeats'.
            Arguments:
                query_id: id of the query.
                top_n: Ranked results are stored in ascendant order by
                       their score. This parameter indicates the number
                       of ranked results (starting form the first one)
                       for which to return the features.
            Returns:
                On success it returns a list with the features for
                each ranked result. It returns False otherwise.
        """
        func_in = {}
        func_in["func"] = "getRankedFeatures"
        func_in["query_id"] = query_id
        func_in["top_n"] = top_n
        request = json.dumps(func_in)

        response = self.custom_request(request)

        func_out = json.loads(response)
        if func_out[SUCCESS_FIELD]:
            return func_out["rfeats"]

        return False


    def test_func(self):
        """
            Simple test function, which will invoke 'testFunc' in the backend
            with three parameters: two strings and one integer.
            Returns:
                The response of testFunc' coming from the backend
        """
        func_in = {}
        func_in["func"] = "testFunc"
        func_in["strparam1"] = "hello"
        func_in["strparam2"] = "there"
        func_in["intparam"] = 47
        request = json.dumps(func_in)

        response = self.custom_request(request)

        print "done testing"
        print response


if __name__ == "__main__":
    # if invoked from the command line, just start the session with the backend
    PORT = 35200
    HOST = "localhost"
    SESSION = Session(port=PORT, host=HOST, verbose=True)
