# -*- coding: UTF-8 -*-
from importlib import import_module
from os import remove, stat, walk
from os.path import expanduser
from pathlib import Path as BasePath
from random import choice
from shutil import rmtree
from six import string_types
from tempfile import gettempdir, NamedTemporaryFile as TempFile

from .utils import LINUX, DARWIN, PYTHON3, WINDOWS


__all__ = __features__ = ["Path", "TempPath"]


class Path(BasePath):
    """ Extension of the base class Path from pathlib.
    
    :param expand: expand user's path
    :param create: create the directory if it doesn't exist
    """
    _flavour = BasePath()._flavour  # fix to AttributeError
    
    def __new__(cls, *parts, **kwargs):
        expand = kwargs.pop("expand", False)
        create = kwargs.pop("create", False)
        _ = super(Path, cls).__new__(cls, *parts, **kwargs)
        if expand:
            _ = _.expanduser().absolute()
        if create and not _.exists():
            _.mkdir(parents=True)  # exist_ok does not work in Python 2
        return _
    
    @property
    def bytes(self):
        """ Get file's content as bytes. """
        with self.open('rb') as f:
            return f.read()
    
    @property
    def child(self):
        """ Get the child path relative to self's one. """
        return Path(*self.parts[1:])
    
    @property
    def filename(self):
        """ Get the file name, without the complete path. """
        return self.stem + self.suffix
    
    @property
    def size(self):
        """ Get path's size. """
        if self.is_file() or self.is_symlink():
            return self.stat().st_size
        elif self.is_dir():
            s = 4096  # include the size of the directory itself
            for root, dirs, files in walk(str(self)):
                s += 4096 * len(dirs)
                for f in files:
                    s += stat(str(Path(root).joinpath(f))).st_size
            return s
    
    @property
    def text(self):
        """ Get file's content as a string. """
        return self.read_text()
    
    def __add_text(self, data, mode='w', encoding=None, errors=None):
        """ Allows to write/append text to the file, both in Python 2 and 3. """
        if not isinstance(data, str if PYTHON3 else string_types):
            raise TypeError("data must be str, not %s" % 
                            data.__class__.__name__)
        with self.open(mode=mode, encoding=encoding, errors=errors) as f:
            return f.write(data)
    
    def append_bytes(self, data):
        """ Allows to append bytes to the file, as only write_bytes is available
             in pathlib, overwritting the former bytes at each write. """
        with self.open(mode='ab') as f:
            return f.write(memoryview(data))
    
    def append_line(self, line):
        """ Shortcut for appending a single line (text with newline). """
        self.append_text(["\n", ""][self.size == 0] + line)
    
    def append_lines(self, *lines):
        """ Shortcut for appending a bunch of lines. """
        for line in lines:
            self.append_line(line)
    
    def append_text(self, text, encoding=None, errors=None):
        """ Allows to append text to the file, as only write_text is available
             in pathlib, overwritting the former text at each write. """
        return self.__add_text(text, 'a', encoding, errors)
    
    def choice(self, *filetypes):
        """ Return a random file from the current directory. """
        if not self.is_dir():
            return self
        filetypes = list(filetypes)
        while len(filetypes) > 0:
            filetype = choice(filetypes)
            filetypes.remove(filetype)
            l = list(self.iterfiles(filetype, filename_only=True))
            if len(l) > 0:
                return self.joinpath(choice(l))
    
    def expanduser(self):
        """ Fixed expanduser() method, working for both Python 2 and 3. """
        return Path(expanduser(str(self)))
    
    def generate(self, prefix="", suffix="", length=8,
                 alphabet="0123456789abcdef"):
        """ Generate a random folder name. """
        if not self.is_dir():
            return self
        while True:
            _ = "".join(choice(alphabet) for i in range(length))
            new = self.joinpath(str(prefix) + _ + str(suffix))
            if not new.exists():
                return new
    
    def is_hidden(self):
        """ Check if the current path is hidden. """
        if DARWIN:
            fnd = import_module("Foundation")
            u, f = fnd.NSURL.fileURLWithPath_(str(self)), fnd.NSURLIsHiddenKey
            return u.getResourceValue_forKey_error_(None, f, None)[1]
        elif LINUX:
            return self.stem.startswith(".")
        elif WINDOWS:
            import win32api, win32con
            return win32api.GetFileAttributes(p) & \
                   (win32con.FILE_ATTRIBUTE_HIDDEN | \
                    win32con.FILE_ATTRIBUTE_SYSTEM)
        raise NotImplementedError("Cannot check for the hidden status on this"
                                  " platform")
    
    def is_samepath(self, otherpath):
        """ Check if both paths have the same parts. """
        return self.absolute().parts == Path(otherpath).absolute().parts
    
    def iterfiles(self, filetype=None, filename_only=False):
        """ List all files from the current directory. """
        for i in self.iterdir():
            if i.is_file() and (filetype is None or i.suffix == filetype):
                    yield i.filename if filename_only else i
    
    def iterpubdir(self):
        """ List all visible subdirectories from the current directory. """
        for i in self.iterdir():
            if i.is_dir() and not i.is_hidden():
                yield i
    
    def mkdir(self, mode=0o777, parents=False, exist_ok=False):
        """ Fix to non-existing argument exist_ok in Python 2. """
        arg = (exist_ok, ) if PYTHON3 else ()
        super(Path, self).mkdir(mode, parents, *arg)
    
    def read_text(self, encoding=None, errors=None):
        """ Fix to non-existing method in Python 2. """
        with self.open(mode='r', encoding=encoding, errors=errors) as f:
            return f.read()
    
    def reset(self):
        """ Ensure the file exists and is empty. """
        with self.open('w') as f:
            pass
    
    def remove(self):
        """ Extension for removing a directory or a file. """
        if self.is_dir():
            rmtree(str(self))
        else:
            remove(str(self))
    
    def write_text(self, data, encoding=None, errors=None):
        """ Fix to non-existing method in Python 2. """
        return self.__add_text(data, 'w', encoding, errors)


class TempPath(Path):
    """ Extension of the class Path for handling a temporary path.
    
    :param length:   length for the folder name (if 0, do not generate a folder
                      name, e.g. keeping /tmp)
    :param alphabet: character set to be used for generating the folder name
    """
    def __new__(cls, **kwargs):
        kw = {}
        kw["prefix"]   = kwargs.pop("prefix", "")
        kw["suffix"]   = kwargs.pop("suffix", "")
        kw["length"]   = kwargs.pop("length", 0)
        kw["alphabet"] = kwargs.pop("alphabet", "0123456789abcdef")
        _ = Path(gettempdir())
        kwargs["create"] = True   # force creation
        kwargs["expand"] = False  # expansion is not necessary
        if kw["length"] > 0:
            while True:
                # ensure this is a newly generated path
                tmp = _.generate(**kw)
                if not tmp.exists():
                    break
            return super(TempPath, cls).__new__(cls, tmp, **kwargs)
        return super(TempPath, cls).__new__(cls, _, **kwargs)
    
    def tempfile(self, **kwargs):
        """ Create a NamedTemporaryFile in the TempPath. """
        kwargs.pop("dir", None)
        return TempFile(dir=str(self), **kwargs)