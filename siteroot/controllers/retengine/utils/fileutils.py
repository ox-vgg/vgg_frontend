#!/usr/bin/env python

import os

def delete_directory_contents(path):
    """
        Utility function to delete the contents of a directory.
        It generates the tree of the directory and makes the deletion
        of each file/folder on the tree from the bottom up.
        Arguments:
           path: Full path to the directory to be deleted.
    """
    empty_dirs = []
    print 'Removing directory contents of path: ' + path

    def delete_files(dir_list, dir_path):
        """
            Private function to delete all files within a directory.
            Arguments:
               dir_list: List of filenames
               dir_path: Full path to the directory containing the files
                         in dir_list.
        """
        for file in dir_list:
            print 'Removing file: ' + os.path.join(dir_path, file)
            os.remove(os.path.join(dir_path, file))

    def remove_directory(dir_entry):
        """
            Private function to remove a directory and its contents.
            Arguments:
               dir_entry: 3-tuple (dirpath, dirnames, filenames). dirname is the
                          path to the directory to be deleted, dirnames is the list
                          of its subfolders, and filenames is the list of files
                          contained in dirname.
        """
        delete_files(dir_entry[2], dir_entry[0])
        empty_dirs.insert(0, dir_entry[0])

    tree = os.walk(path)
    for directory in tree:
        remove_directory(directory)

    for dir in empty_dirs:
        if not os.path.samefile(path, dir):
            print 'Removing directory: ' + dir
            os.rmdir(dir)
