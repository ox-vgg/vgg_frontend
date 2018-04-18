#!/usr/bin/env python

import re
import urllib
from hashlib import md5
try:
    import simplejson as json
except ImportError:
    import json  # Python 2.6+ only

from retengine import models


def get_query_strid(query, escape=False):
    """
        Utility function to generate the string id of a query
        Arguments:
            query: query dictionary
            escape: boolean indicating to escape special characters in the string
        Returns:
            a string id
    """
    # formulate string identifier for the query definition
    queryhash = md5(json.dumps(query['qdef'])).hexdigest()
    queryhash = queryhash[0:8]

    if isinstance(query['qdef'], basestring):
        querystr = query['qdef']
        if escape:
            querystr = escape_querystr(querystr)
        # can't include hash, as this breaks caching
        #querystr = '{%s}[%s]' % (querystr, queryhash[0:5])
        querystr = '{%s}' % querystr
    else:
        querystr = queryhash

    # add previous qsid if present (to show source of query)
    if 'prev_qsid' in query and query['prev_qsid']:
        prev_qsid_str = query['prev_qsid']
        prev_qsid_str = prev_qsid_str[0:min(len(prev_qsid_str), 5)]
        querystr = 'prevqsid[%s]__%s' % (prev_qsid_str, querystr)

    # combine with query identifier for the query type
    query_strid = '%s__%s' % (query['qtype'], querystr)

    return query_strid


def decode_query_strid(strid, escape=False):
    """
        Utility function to decode a query out of a string id.
        Only queries of type 'text' can be decoded.
        Arguments:
            strid: string id of a query
            escape: boolean indicating to unescape special characters in the string
        Returns:
            a tuple (query text, query type)
    """
    qtype = strid.split('__', 1)[0]

    if qtype != models.opts.Qtypes.text:
        raise models.errors.StrIdDecodeError("Only queries of type 'text' can be decoded")

    try:
        querystr = re.search('(?<=\{).+(?=\})', strid).group()
        if escape:
            querystr = unescape_querystr(querystr)
    except:
        raise models.errors.StrIdDecodeError("Could not parse query text from query string")

    return (querystr, qtype)


def escape_querystr(querystr):
    """
        Utility function to escape special characters in a string.
        Currently escaping: ' " / ; : ,
        Arguments:
            querystr: input string
        Returns:
            input string with escaped characters.
    """
    query_esc = querystr.replace("'", '_-_')
    query_esc = query_esc.replace('"', '_--_')
    query_esc = query_esc.replace('/', '-_-')
    query_esc = query_esc.replace(';', '_____')
    query_esc = query_esc.replace(':', '____')
    query_esc = query_esc.replace(',', '___')
    query_esc = urllib.quote(query_esc)
    return query_esc


def unescape_querystr(query_esc):
    """
        Utility function to unescape special characters in a string.
        Currently unescaping: ' " / ; : ,
        Arguments:
            querystr: escaped input string
        Returns:
            input string with unescaped characters.
    """
    querystr = query_esc.replace('_-_', "'")
    querystr = querystr.replace('_--_', '"')
    querystr = querystr.replace('-_-', '/')
    querystr = querystr.replace('_____', ';')
    querystr = querystr.replace('____', ':')
    querystr = querystr.replace('___', ',')
    querystr = urllib.unquote(querystr)
    return querystr
