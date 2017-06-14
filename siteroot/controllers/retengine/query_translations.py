import string
from hashlib import md5
try:
    import simplejson as json
except ImportError:
    import json  # Python 2.6+ only
import validictory
import models


def querystr_tuple_to_query(querystr, qtype, dsetname, engine, prev_qsid=None):
    """
        Takes the query given in the parameters and converts it to a dictionary.
        Arguments:
           querystr: query string as sent by the frontend.
           qtype: query type. This value determines whether querystr corresponds to just
                  the string in the query or if it also encodes more information.
           dsetname: dataset name
           engine: engine name
           prev_qsid: previous query id. Only used when refining a previous query.
        Returns:
           The query in dictionary form.
           It will rise a ValueError exception if the dictionary structure does not fit
           json_schema.query_schema.
    """
    query = {'qtype': qtype, 'dsetname': dsetname}
    if qtype == models.opts.qtypes.text:
        query['qdef'] = querystr
    else:
        query['qdef'] = decode_image_querystr(querystr)

    if engine:
        query['engine'] = engine

    # store optional previous query session id param if it was provided
    if prev_qsid:
        query['prev_qsid'] = prev_qsid

    # validate converted input just in case...
    validictory.validate(query, models.json_schema.query_schema)

    return query


def query_to_querystr_tuple(query):
    """
        Takes the given query in form of a dictionary and converts it to a tuple.
        Arguments:
           query: query in dictionary form.
        Returns: A tuple containing:
           querystr: query string as sent by the frontend.
           qtype: query type.
           dsetname: dataset name.
           engine: engine name.
    """
    querystr = query_to_querystr(query)

    return (querystr, query['qtype'], query['dsetname'], query['engine'] )


def query_to_querystr(query):
    """
        Return the query made by the user in string form. If the query type is 'text'
        this should correspond to just the original string entered by the user. Otherwise
        it could contains other information, such as the path to an image or even a ROI
        definition.
        Arguments:
           query: query in dictionary form.
        Returns:
           query string as sent originally by the frontend.
    """
    if query['qtype'] == models.opts.qtypes.text:
        querystr = query['qdef']
    else:
        querystr = encode_image_querystr(query['qdef'])

    return querystr


def get_qhash(query, include_engine=True, include_qtype=True, include_dsetname=True):
    """
        Computes a hash of the query. This is later used as an identifier of the query
        for the cache and other purposes.
        Arguments:
           query: query in dictionary form.
           include_engine: Boolean indicating whether to include the engine name in the returned value
           include_qtype: Boolean indicating whether to include the query type in the returned value
           include_dsetname: Boolean indicating whether to include the dataset name in the returned value
        Returns:
           A md5 hash of the query, possibly also including the engine name and/or the query type and/or
           the dataset name, depending on the value of the parameters.
    """
    # store query hash lazily in query object
    if 'qhash' not in query:
        query['qhash'] = md5(json.dumps(query['qdef'])).hexdigest()

    qhash_out = query['qhash']
    if include_qtype:
        qhash_out = '%s__%s' % (query['qtype'], qhash_out)
    if include_dsetname:
        qhash_out = '%s_%s' % (query['dsetname'], qhash_out)
    if include_engine:
        qhash_out = '%s_%s' % (query['engine'], qhash_out)

    return qhash_out


def decode_image_querystr(querystr):
    """
        Converts the query string of an image search into a dictionary.
        Arguments:
           querystr: query string as sent originally by the frontend.
        Returns:
           A dictionary containing the paths to the images in the queries and
           any extra parameters like ROIs or annotation values.
    """
    output = []
    images = querystr.split(';') # images separated by ';'
    for image_data in images:
        params = image_data.split(',') # parameters separated by ','
        image = dict()
        image['image'] = params[0]
        image['extra_params'] = dict()
        if len(params) > 1:
            params = params[1:]
            for param_str in params:
                ext_param = param_str.split(':')
                if ext_param[0] == 'roi':
                    ext_param[1] = ext_param[1].split('_')
                    ext_param[1] = map(float, ext_param[1])
                if ext_param[0] == 'anno':
                    ext_param[1] = int(ext_param[1])

                image['extra_params'][ext_param[0]] = ext_param[1]

        output.append(image)
    return output


def encode_image_querystr(data):
    """
        Encodes the query data of an image search into a string.
        Arguments:
           data: image query data
        Returns:
           A string containing the paths to the images in the queries and
           any extra parameters like ROIs or annotation values.
    """
    qstr = ''

    for image in data:
        qstr = qstr + image['image']
        if 'extra_params' in image:
            if len(image['extra_params'])>0:
                for param,value in image['extra_params'].iteritems():
                    if param == 'anno':
                        value = str(value)
                    elif param == 'roi':
                        roi_str = '%d_%d_%d_%d_%d_%d_%d_%d_%d_%d' % tuple(value)
                        value = roi_str
                    qstr = qstr + ',' + param + ':' + value
        qstr = qstr + ';'

    qstr = qstr[0:-1]

    return qstr
