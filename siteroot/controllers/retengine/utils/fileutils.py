#!/usr/bin/env python

import os
import platform
import shutil


def delete_directory_subdirectories(path, name_filter=None):
    """
        Utility function to delete all subdirectories of a directory.
        Arguments:
           path: Full path to the directory which subdirectories should be deleted.
           name_filter: When different to 'None', a string that must be
                        contained in a folder name in order to delete it.
    """

    def samefile(file1, file2):
        """
            Checks the stats of two files in an attempt to determine if they are the same.
            Arguments:
               file1: filepath of the first file
               file2: filepath of the second file
        """
        return os.stat(file1) == os.stat(file2)

    print ('Removing subdirectories of path: ' + path)
    for root, dirnames, filenames in os.walk(path):
        for subdir in dirnames:
            if name_filter:
                if name_filter in subdir:
                    subdir_path = os.path.join(root, subdir)
                    if 'Windows' not in platform.system():
                        if not os.path.samefile(path, subdir_path):
                            print ('Removing directory: ' + subdir_path)
                            shutil.rmtree(subdir_path)
                    else:
                        # os.path.samefile not available in Windows
                        if not samefile(path, subdir_path):
                            print ('Removing directory: ' + subdir_path)
                            shutil.rmtree(subdir_path)
            else:
                subdir_path = os.path.join(root, subdir)
                if 'Windows' not in platform.system():
                    if not os.path.samefile(path, subdir_path):
                        print ('Removing directory: ' + subdir_path)
                        shutil.rmtree(subdir_path)
                else:
                    # os.path.samefile not available in Windows
                    if not samefile(path, subdir_path):
                        print ('Removing directory: ' + subdir_path)
                        shutil.rmtree(subdir_path)


def delete_directory_contents(path, name_filter=None):
    """
        Utility function to delete the contents of a directory.
        It generates the tree of the directory and makes the deletion
        of each file/folder on the tree from the bottom up.
        Arguments:
           path: Full path to the directory to be deleted.
           name_filter: When different to 'None', a string that must be
                        contained in a filename in order to delete it.
    """
    empty_dirs = []
    print ('Removing directory contents of path: ' + path)

    def delete_files(dir_list, dir_path, name_filter=None):
        """
            Private function to delete all files within a directory.
            Arguments:
               dir_list: List of filenames
               dir_path: Full path to the directory containing the files
                         in dir_list.
               name_filter: When different to 'None', a string that must be
                            contained in a filename in order to delete it.
        """
        deleted_file_counter = 0
        for afile in dir_list:
            if name_filter:
                if name_filter in afile:
                    print ('Removing file: ' + os.path.join(dir_path, afile))
                    os.remove(os.path.join(dir_path, afile))
                    deleted_file_counter = deleted_file_counter + 1
            else:
                print ('Removing file: ' + os.path.join(dir_path, afile))
                os.remove(os.path.join(dir_path, afile))
                deleted_file_counter = deleted_file_counter + 1

        return deleted_file_counter == len(dir_list)

    def remove_directory(dir_entry, name_filter=None):
        """
            Private function to remove a directory and its contents.
            Arguments:
               dir_entry: 3-tuple (dirpath, dirnames, filenames). dirname is the
                          path to the directory to be deleted, dirnames is the list
                          of its subfolders, and filenames is the list of files
                          contained in dirname.
               name_filter: When different to 'None', a string that must be
                            contained in a filename in order to delete it.
        """
        if delete_files(dir_entry[2], dir_entry[0], name_filter):
            empty_dirs.insert(0, dir_entry[0])

    def samefile(file1, file2):
        """
            Checks the stats of two files in an attempt to determine if they are the same.
            Arguments:
               file1: filepath of the first file
               file2: filepath of the second file
        """
        return os.stat(file1) == os.stat(file2)

    tree = os.walk(path)
    for directory in tree:
        remove_directory(directory, name_filter)

    if 'Windows' not in platform.system():
        for adir in empty_dirs:
            if not os.path.samefile(path, adir):
                print ('Removing directory: ' + adir)
                os.rmdir(adir)
    else:
        # os.path.samefile not available in Windows
        for adir in empty_dirs:
            if not samefile(path, adir):
                print ('Removing directory: ' + adir)
                os.rmdir(adir)
