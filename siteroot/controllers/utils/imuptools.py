#!/usr/bin/env python

import urllib2
import os
import uuid
import base64
import imchecktools


class ImageUploader:
    """ Class with utility functions to upload an image """

    def __init__(self, upload_dir, maximwidth=-1, maximheight=-1):
        """
            Initializes the class and sets the uploading directory.
            Arguments:
                upload_dir: Directory where to upload the images.
                maximwidth: Maximum allowed width
                maximheight: Maximum allowed height.
        """
        self.upload_dir = upload_dir
        self.maximwidth = maximwidth
        self.maximheight = maximheight


    def get_localimg_from_file(self, filename):
        """
            Uploads an image from a filepath
            Arguments:
                filename: Full path of the file to be uploaded
            Returns:
                The full path to the uploaded file.
        """
        (localdir, localfilenames) = self.get_localimgs_from_files([filename,])
        return os.path.join(localdir, localfilenames[0])


    def get_localimg_from_imgdata(self, img_data, is_data_base64=False):
        """
            Saves the data of an image into a file in a randomly-named-subfolder
            inside the uploading directory.
            Arguments:
                img_data: Image binary data
                is_data_base64: Boolean indicating whether img_data is encoded in base64 or not.
            Returns:
                A pair (localdir, localfilename) where localdir is the
                name of the created randomly-named-subfolder and localfilename
                is the of the file created with img_data.
        """
        localdir = str(uuid.uuid4())
        print 'Getting local image from file(s)'
        localfilenames = []
        remotefilename = img_data['filename'];
        localpath = os.path.join(self.upload_dir, localdir)

        if not os.path.isdir(localpath):
            os.makedirs(localpath, 0755)
        localfilepath = os.path.join(localpath, remotefilename)
        print '  ->' + localfilepath
        localfile = open(localfilepath, 'wb')
        if is_data_base64:
            data = base64.b64decode(img_data['data'])
        else:
            data = img_data['data']
        localfile.write(data)
        localfile.close()
        print '  Image Written'

        localfilepath = imchecktools.verify_image(localfilepath,
                                                  self.maximwidth,
                                                  self.maximheight)
        print '  Image verified'

        localfilenames.append(remotefilename)

        return os.path.join(localdir, localfilenames[0])


    def get_localimgs_from_files(self, files):
        """
            Uploads a set of images from a set of filepaths.
            It creates a randomly-named-subfolder inside the uploading
            directory and stores the images there.
            Arguments:
                files: List of paths of the files to be uploaded
            Returns:
                A pair (localdir, localfilenames) where localdir is the
                name of the created randomly-named-subfolder and localfilenames
                is the list of names for the uploaded files.
        """
        localdir = str(uuid.uuid4())
        print 'Getting local image from file(s)'
        localfilenames = []
        for src_filepath in files:
            src_filename = os.path.basename(src_filepath)
            localpath = os.path.join(self.upload_dir, localdir)
            if not os.path.isdir(localpath):
                os.makedirs(localpath, 0755)
            dest_filepath = os.path.join(localpath, src_filename)
            print '  ->' + dest_filepath
            with open(src_filepath, 'rb') as src_file:
                data = src_file.read()
                with open(dest_filepath, 'wb') as dest_file:
                    dest_file.write(data)
            print '  Image Written'

            localfilepath = imchecktools.verify_image(dest_filepath,
                                                      self.maximwidth,
                                                      self.maximheight)
            print '  Image verified'

            localfilenames.append(src_filename)

        return (localdir, localfilenames)


    def get_localimg_from_url(self, url, timeout=30):
        """
            Uploads an image from an url.
            It creates a randomly-named-subfolder inside the uploading
            directory and downloads the image there.
            Arguments:
                url: URL to the file to be uploaded.
                timeout: Number of seconds before timing out when downloading the image.
            Returns:
                A pair (localdir, localfilename) where localdir is the
                name of the created randomly-named-subfolder and localfilename
                is the name of the uploaded file.
        """
        (localdir, localfilenames) = self.get_localimgs_from_urls([url,], timeout)
        return os.path.join(localdir, localfilenames[0])


    def get_localimgs_from_urls(self, urls, timeout=30):
        """
            Uploads a set of images from a set of urls.
            It creates a randomly-named-subfolder inside the uploading
            directory and downloads the images there.
            Arguments:
                urls: List of urls to the files to be uploaded.
                timeout: Number of seconds before timing out when downloading each image.
            Returns:
                A pair (localdir, localfilenames) where localdir is the
                name of the created randomly-named-subfolder and localfilenames
                is the list of names for the uploaded files.
        """
        localdir = str(uuid.uuid4())
        print 'Getting local image from url(s)'
        localfilenames = []
        for url in urls:
            remotefilename = os.path.basename(url)
            localpath = os.path.join(self.upload_dir, localdir)
            if not os.path.isdir(localpath):
                os.makedirs(localpath, 0755)
            localfilepath = os.path.join(localpath, remotefilename)
            print '  ' + url + '->' + localfilepath
            opener = urllib2.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0')] # pretend to be firefox
            img = opener.open(url, None, timeout)

            localfile = open(localfilepath, 'wb')
            localfile.write(img.read())
            localfile.close()
            print '  Image Written'

            localfilepath = imchecktools.verify_image(localfilepath,
                                                      self.maximwidth,
                                                      self.maximheight)
            print '  Image verified'

            localfilenames.append(remotefilename)

        return (localdir, localfilenames)
