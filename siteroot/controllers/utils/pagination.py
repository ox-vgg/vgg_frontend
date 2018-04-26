#!/usr/bin/env python

import math

class PageManager(object):
    """ Class with utility functions for managing array of pages """

    def __init__(self, page_len, page_array_len=15):
        """
            Initializes the class and sets the length of the pages and
            the array of pages
            Arguments:
                page_len: Number of elements per page
                page_array_len: Length of page numbers array
        """
        self.page_len = page_len
        self.page_array_len = page_array_len


    def construct_page_array(self, page, num_pages):
        """
            Construct an array of visible pages for display.
            Utility function for computing an array of adjacent result
            pages given a number representing the currently active page.
            Arguments:
                page: Current page number
                num_pages: Total number of pages
            Returns:
                A list of adjacent page numbers
        """
        mid_page = int(math.ceil(self.page_array_len / 2.0))
        page_start = 1
        page_end = self.page_array_len
        if page > mid_page:
            if page < num_pages - mid_page + 2:
                page_start = page - mid_page + 1
                page_end = page + mid_page - 1
            else:
                page_start = num_pages - self.page_array_len + 1
                page_end = num_pages
        if page_end > num_pages:
            page_end = num_pages
        if page_start < 1:
            page_start = 1
        pages = range(page_start, page_end + 1)

        return pages


    def get_page(self, rlist, page):
        """
            Extract the elements of the given page from the full list
            of elements.
            Arguments:
                rlist: Full list of elements
                page: Number of the page to be retrieved
            Returns:
                A pair (a,b) where 'a' corresponds to the elements
                in the requested page and 'b' corresponds to the
                total number of pages that can be built from rlist.
        """
        item_count = len(rlist)
        num_pages = int(math.ceil(float(item_count) / self.page_len))

        min_idx = 0
        max_idx = item_count
        if page > num_pages:
            page = num_pages
        if page > 0:
            min_idx = (page - 1) * self.page_len
            max_idx = page * self.page_len

        return (rlist[min_idx:max_idx], num_pages)
