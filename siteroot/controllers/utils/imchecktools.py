#!/usr/bin/env python

import os
from PIL import Image


class ImageExtfindError(Exception):
    """ Class for reporting errors related to the problems with the image extension/format """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


def verify_image(filename, maxwidth=None, maxheight=None):
    """
        Opens an image and checks if it is valid. If the image's
        width or height exceed the specified maximums, the image
        is resized.
        Arguments:
            filename: Path to the image to be checked.
            maxwidth: Maximum allowed width
            maxheight: Maximum allowed height
        Returns:
            It returns the image path is the image is valid.
            It raises IOError if the image cannot be opened or resized.
            It raises ImageExtfindError if the image extension/format cannot be recognized.
    """
    im = Image.open(filename)
    imformat = None
    try:
        (imwidth, imheight) = im.size
        im.verify()
        imformat = im.format

        sf = 1.0
        sf2 = 1.0
        if maxwidth > 0 and imwidth > maxwidth:
            sf = float(maxwidth)/float(imwidth)
        if maxheight > 0 and imheight > maxheight:
            sf2 = float(maxheight)/float(imheight)
        if sf2 < sf:
            sf = sf2
        if sf < 1.0:
            im = Image.open(filename)
            newimwidth = int(imwidth*sf)
            newimheight = int(imheight*sf)
            im = im.resize((newimwidth, newimheight), Image.ANTIALIAS)
            im.save(filename, format=imformat)
        else:
            im = Image.open(filename)
            im.save(filename, format=imformat)
    except Exception as e:
        print ('Exception while verifying image', e)
        raise IOError

    # now see if a valid extension has been specified (required)
    unused_root, fileext = os.path.splitext(filename)
    if (fileext == '') or (fileext.find('?') != -1):
        # if there is no valid extension supplied, then try to extract
        # this using the loaded image...
        if imformat != None:
            impath = filename + '.' + imformat.lower()
            im.save(impath, imformat)
        else:
            raise ImageExtfindError(filename)
    else:
        impath = filename

    return impath
