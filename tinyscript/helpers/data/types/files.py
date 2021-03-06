# -*- coding: UTF-8 -*-
"""Files/Folders-related checking functions and argument types.

"""
import re
from magic import from_file
from os import access, makedirs, X_OK
from os.path import exists, isdir, isfile

from .strings import _str2list


__all__ = __features__ = []


# dummy shortcuts, compliant with the is_* naming convention
__all__ += ["is_dir", "is_executable", "is_file", "is_filetype", "is_folder", "is_mimetype"]
is_dir = is_folder = isdir
is_executable = lambda f: access(f, X_OK)
is_file = isfile
is_filetype = lambda f, t: is_file(f) and re.search(t, from_file(f)) is not None
is_mimetype = lambda f, m: is_file(f) and re.search(m, from_file(f, mime=True)) is not None


# file and folder-related argument types
__all__ += ["file_does_not_exist", "file_exists", "file_mimetype", "file_type", "files_list", "files_mimetype",
            "files_type", "files_filtered_list", "folder_does_not_exist", "folder_exists",
            "folder_exists_or_create"]


def file_does_not_exist(f):
    """ Check that the given file does not exist. """
    if exists(f):
        raise ValueError("'{}' already exists".format(f))
    return f
folder_does_not_exist = file_does_not_exist


def file_exists(f):
    """ Check that the given file exists. """
    if not exists(f):
        raise ValueError("'{}' does not exist".format(f))
    if not isfile(f):
        raise ValueError("Target exists and is not a file")
    return f


def __file_type(mime=False):
    """ Check that the given file has the given {} type. """
    def _wrapper(ftype):
        def _subwrapper(f):
            if file_exists(f) and not [is_filetype, is_mimetype][mime](f, ftype):
                raise ValueError("Target's type is not {}".format(ftype))
            return f
        return _subwrapper
    return _wrapper
file_mimetype, file_type = __file_type(True), __file_type()
file_mimetype.__doc__ = __file_type.__doc__.format("MIME")
file_type.__doc__ = __file_type.__doc__.format("file")


def files_list(l, filter_bad=False):
    """ Check if the list contains valid files. """
    l = _str2list(l)
    nl = []
    for f in l:
        if not isfile(f):
            if not filter_bad:
                raise ValueError("A file from the given list does not exist")
        else:
            nl.append(f)
    if filter_bad and len(nl) == 0:
        raise ValueError("No valid file in the given list")
    return nl


def __files_type(mime=False):
    """ Check if the list contains valid file types. """
    def _wrapper(ftype):
        def _subwrapper(l):
            for f in files_list(l):
                __file_type(mime)(ftype)(f)
            return l
        return _subwrapper
    return _wrapper
files_mimetype, files_type = __files_type(True), __files_type()
files_mimetype.__doc__ = files_type.__doc__ = __files_type.__doc__


def files_filtered_list(l):
    """ Check if the list contains valid files and discard invalid ones. """
    return files_list(l, True)


def folder_exists(f):
    """ Check that the given folder exists. """
    if not exists(f):
        raise ValueError("'{}' does not exist".format(f))
    if not isdir(f):
        raise ValueError("Target exists and is not a folder")
    return f


def folder_exists_or_create(f):
    """ Check that the given folder exists and create it if not existing. """
    if not exists(f):
        makedirs(f)
    if not isdir(f):
        raise ValueError("Target exists and is not a folder")
    return f

