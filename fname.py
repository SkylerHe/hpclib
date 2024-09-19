# -*- coding: utf-8 -*-
import typing
from   typing import *

###
# Standard imports, starting with os and sys
###
min_py = (3, 11)
import os
import sys
if sys.version_info < min_py:
    print(f"This program requires Python {min_py[0]}.{min_py[1]}, or higher.")
    sys.exit(os.EX_SOFTWARE)

###
# Other standard distro imports
###
import argparse
from   collections.abc import *
import contextlib
import getpass
import logging

###
# Installed libraries like numpy, pandas, paramiko
###
from functools import total_ordering
from urllib.parse import urlparse
###
# From hpclib
###
import linuxutils
from   urdecorators import trap
from   urlogger import URLogger

###
# imports and objects that were written for this project.
###
import fcntl
import hashlib
import io
try:
    import xxhash
    hasher = xxhash.xxh64()
except ImportError:
    hasher = hashlib.sha1()
###
# Global objects
###
mynetid = getpass.getuser()
logger = None
###
# Credits
###
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2024, University of Richmond'
__credits__ = None
__version__ = 0.1
__maintainer__ = 'George Flanagin, Skyler He'
__email__ = 'gflanagin@richmond.edu, yingxinskyler.he@gmail.com'
__status__ = 'in progress'
__license__ = 'MIT'

class Fname:
    """This is an empty class for demonstration purposes."""
@total_ordering
class Fname:
    """
    A portable class for manipulating long, complex, and potentially confusing file paths on both Linux and Windows systems.

    The `Fname` class provides an abstraction for handling file paths in a way that is consistent across different operating systems.
    It supports all standard comparison operators (==, !=, <, <=, >, >=) by using the fully qualified file path, ensuring that
    file comparisons are accurate regardless of the system's file path conventions.

    Example:
        f = Fname('/home/data/import/big.file.dat')
    
    This instance of `Fname` can be used for various file path manipulations, and the same logic will work on Windows NTFS with the 
    path written as `\\home\\data\\import\\big.file.dat`.

    Features:
        - Portably handles file paths across Linux and Windows.
        - Supports all comparison operators, using the fully qualified path for comparisons.
        - Provides utility functions for checking file existence, path manipulation, and other common operations.
        - Returns the fully qualified name when the object is converted to a string, allowing easy retrieval of the full file path.

    Usage:
        - Initialize an `Fname` object with a file path.
        - Use comparison operators to compare file paths.
        - Check file existence by simply using the object in an `if` statement.
        - Use `str()` to get the fully qualified path of the file.

    Example Usage:
        f = Fname('file.ext')
        if not f:
            raise FileNotFoundError("The file does not exist.")
        print(str(f))  # Outputs the fully qualified file path.

    Note:
        This class is especially useful for developers working in cross-platform environments where file path manipulations need to
        be consistent and error-free, regardless of the underlying operating system.
    """

    BUFSIZE = io.DEFAULT_BUFFER_SIZE
    __slots__ = {
        '_me' : 'The name as it appears in the constructor',   # 0
        '_is_URI' : 'True or False based on containing a "scheme"',  # 1
        '_fqn' : 'Fully resolved name', # 2
        '_dir' : 'Just the directory part of the name', # 3
        '_fname' : 'Just the file and the extension', # 4
        '_fname_only' : 'No directory and no extension', # 5
        '_ext' : 'Just the extension (if there is one)', # 6
        '_all_but_ext' : 'The whole thing, minus any extension', # 7
        '_len' : 'save the length', # 8
        '_inode' : 'the inode identifier', # 9
        '_nlink' : 'number of links to the inode', # 10
        '_content_hash' : 'hexdigit string representing the hash of the contents at last reading', # 11
        '_edge_hash' : 'hash of the first and last disc page of the file.', # 12
        '_lock_handle' : 'an entry in the logical unit table.' # 13
        }

    __values__ = ( None, False, '', '', '', '', '', '', -1, 0, None, '', '', None )
    #               0      1    2   3   4   5   6   7   8   9    10  11  12   13

    __defaults__ = dict(zip(__slots__.keys(), __values__))
    
    def __init__(self, s:str):
        """
        Create an Fname from a string that is a file name or a well
        behaved URI. An Fname consists of several strings, each of which
        corresponds to one of the commonsense parts of the file name.

        Raises a ValueError if the argument is empty.
        """


        if not s or not isinstance(s, str):
            raise ValueError('Cannot create empty Fname object.')

        self._me = s
        for k,v in Fname.__defaults__.items():
            setattr(self, k, v)

        self._is_URI = True if "://" in s else False
        if self._is_URI and 'file://' in s:
            tup = urlparse(s)
            self._fqn = tup.path
        else:
            self._fqn = os.path.abspath(os.path.expandvars(os.path.expanduser(s)))

        self._dir, self._fname = os.path.split(self._fqn)
        self._fname_only, self._ext = os.path.splitext(self._fname)
        self._all_but_ext = self._dir + os.path.sep + self._fname_only
        try:
            result = os.stat(self._fqn)
            self._inode = result.st_ino
            self._len = result.st_size
            self._nlink = result.st_nlink
        except Exception as e:
            pass


    def __bool__(self) -> bool:
        """
        returns: -- True if the Fname object is associated with something
        that exists in the file system AT THE TIME THE FUNCTION IS CALLED.
        Note: this allows one to build the Fname object at a time when "if"
        would return False, open the file for write, test again, and "if"
        will then return True.
        """
        return os.path.isfile(self._fqn)

    def __call__(self, new_content:str=None) -> Union[bytes, Fname]:
        """
        Return the contents of the file as an str-like object, or
        write new content.
        """

        content = ""

        # if the file does not exist, it is empty.
        if not bool(self) and not new_content:
            return content

        # it does exist, and we are reading it.
        elif bool(self) and not new_content:
            with open(str(self), 'r') as f:
                content = f.read()

        # it does not exist, and we are writing it.
        elif not bool(self) and new_content:
            with open(str(self), 'wb+') as f:
                f.write(new_content.encode('utf-8'))

        # it exists, and we are appending.
        else:
            with open(str(self), 'ab') as f:
                f.write(new_content.encode('utf-8'))

        return content if new_content is None else self



        
    def __len__(self) -> int:
        """
        returns -- number of bytes in the file
        """
        if not self: return 0
        if self._len < 0:
            result = os.stat(str(self))
            self._len = result.st_size
            self._inode = result.st_ino
        return self._len


    def __str__(self) -> str:
        """
        returns: -- The fully qualified name.
        str(f) =>> '/home/data/import/big.file.dat'
        """

        return self._fqn


    def __format__(self, x) -> str:
        return self._fqn


    def __eq__(self, other) -> bool:
        """
        The two fname objects are equal if and only if their fully
        qualified names are equal.
        """
        if isinstance(other, Fname):
            return str(self) == str(other)
        elif isinstance(other, str):
            return str(self) == other
        else:
            return NotImplemented


    def __lt__(self, other) -> bool:
        """
        The less than operation is done with the fully qualified names.
        """

        if isinstance(other, Fname):
            return str(self) < str(other)
        elif isinstance(other, str):
            return str(self) < other
        else:
            return NotImplemented


    def __matmul__(self, other) -> bool:
        """
        returns True if the files' contents are the same. We will
        check to ensure that each is really a file that exists, and
        then check the size before we check the contents.
        """
        if not isinstance(other, Fname):
            return NotImplemented

        if not self or not other: return False
        if len(self) != len(other): return False 
        
        if not self._edge_hash: self.edge_hash()
        if not other._edge_hash: other.edge_hash()
        if self._edge_hash != other._edge_hash: return False

        # Gotta look at the contents. See if our hash is known.
        if not self._content_hash: self()

        # Make sure the other object's hash is known.
        if not len(other._content_hash): other()
        return self._content_hash == other._content_hash

    
    @property
    def all_but_ext(self) -> str:
        """
        returns: -- The directory, with the filename stub, but no extension.
        f.all_but_ext() =>> '/home/data/import/big.file' ... note lack of trailing dot
        """

        return self._all_but_ext


    @property
    def busy(self) -> bool:
        """
        returns: --
                True: iff the file exists, we have access, and we cannot
                    get get an exclusive lock.
                None: if the file does not exist, or if it exists and we
                    have no access to the file (therefore we can never
                    lock it).
                False: otherwise.
        """

        # 1: does the file exist?
        if not self: return None

        # 2: if the file is locked by us, then it is not "busy".
        if self.locked: return False

        # 3: are we allowed to open the file?
        if not os.access(str(self), os.R_OK):
            print(f'No access to {self}.')
            return None

        # 4: OK, we are allowed access, but can we open it?
        try:
            fd = os.open(str(self), os.O_RDONLY)
        except Exception as e:
            print(f'Cannot open {self}, so it is busy.')
            return True

        # 5: Can we lock it?
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            print(f'{self} is locked.')
            return False

        except BlockingIOError as e:
            print(f'No lock available on {self}, so it is busy')
            return True

        except Exception as e:
            print(str(e))
            return None

        finally:
            try:
                os.close(fd)
            except:
                pass
    @property
    def directory(self) -> str:
        """
        returns: -- The directory part of the name.
        f.directory() =>> '/home/data/import' ... note the lack of a
            trailing solidus in the default behavior.
        """

      
        return self._dir




    @property
    def empty(self) -> bool:
        """
        Check if the file is absent, inaccessible, or short and containing only whitespace.
        Return:
            -- True if the file is short and containing only whitespace
            -- False otherwise
            -- Error if the file is absent, inaccessible(no read permission) or else
        """
        try:
            # Check if the file exists and is accessible
            if not os.path.isfile(self._fqn):
                print(f"File '{self._fqn}' does not exist.")
                return True
        
            # Check if the file is readable
            if not os.access(self._fqn, os.R_OK):
                print(f"File '{self._fqn}' is not accessible (no read permission).")
                return True
        
            # Check if the file is short (less than 3 bytes) or only contains whitespace
            with open(self._fqn, 'r') as f:
                return len(f.read()) < 3 or not f.read().strip()
    
        except (FileNotFoundError, PermissionError):
            return False

        except Exception as e:
            return None


    @property
    def ext(self) -> str:
        """
        returns: -- The extension, if any.
        f.ext() =>> 'dat'
        """

        return self._ext

    @property
    def fname(self) -> str:
        """
        returns: -- The filename only (no directory), including the extension.
        f.fname() =>> 'big.file.dat'
        """

        return self._fname


    @property
    def fname_only(self) -> str:
        """
        returns: -- The filename only. No directory. No extension.
        f.fname_only() =>> 'big.file'
        """

        return self._fname_only


    @property
    def fqn(self) -> str:
        """
        returns: -- The fully qualified name.
        f.fqn() =>> '/home/data/import/big.file.dat'
        NOTE: this is the same result as you get with str(f)
        """

        return self._fqn


    @property
    def edge_hash(self) -> str:
        """
        Return the hash of the file's content. Initializes the hasher using xxhash first; 
        if unavailable, falls back to SHA-1. The hash is cached after the first computation.
        """
        global hasher
        if self._edge_hash:
            return self._edge_hash
        try:
            with open(str(self), 'rb') as f:
                 hasher.update(f.read(io.DEFAULT_BUFFER_SIZE))
            
            self._edge_hash = hasher.hexdigest()
        
        except:
            self._content_hash = '0000000000000000'   


        return self._edge_hash


    @property
    def hash(self) -> str:
        """
        Return the hash if it has already been calculated, otherwise
        calculate it and then return it.
        """
        global hasher
        
        if self._content_hash:
            return self._content_hash

        try:
            with open(str(self), 'rb') as f:
                _ = [hasher.update(chunk) for chunk in iter(lambda: f.read(io.DEFAULT_BUFFER_SIZE), b'')]
            
            self._content_hash = hasher.hexdigest()

        except:
            self._content_hash = '0000000000000000'

        return self._content_hash


    @property
    def is_URI(self) -> bool:
        """
        Returns true if the original string used in the ctor was
            something like "file://..." or "http://..."
        """

        return self._is_URI


    def lock(self, exclusive:bool = True, nowait:bool = True) -> bool:
        mode = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        if nowait: mode = mode | fcntl.LOCK_NB
        try:
            self._lock_handle = os.open(str(self), os.O_RDONLY)
            fcntl.flock(self._lock_handle, mode)
        except Exception as e:
            print(f"{e}")
            return False
        else:
            return True


    @property
    def locked(self) -> bool:
        """
        Test it...  Note that this function returns True if this process
            has the file locked. self.busy checks if someone else has the
            file locked.
        """
        return self._lock_handle is not None


    def show(self) -> None:
        """
            this is a diagnostic function only. Probably not used
            in production.
        """
        print(f"if test returns {self.__bool__()}")
        print(f"{str(self)=}")
        print(f"{self.fqn=}")
        print(f"{self.fname=}")
        print(f"{self.fname_only=}")
        print(f"{self.directory=}")
        print(f"{self.ext=}")
        print(f"{self.all_but_ext=}")
        print(f"{len(self)=}")
        s = self()
        try:
            print(f"() returns >>>{s[0:30]} .... \n{s[-30:]}<<<\n")
        except TypeError as e:
            print("() doesn't make sense on a binary file.")
        print(f"{self._inode=}")
        print(f"{self.hash=}")
        print(f"{self.edge_hash()=}")
        print(f"{self.locked=}")

    def unlock(self) -> bool:
        """
        returns: -- True iff the file was locked before the call,
            False otherwise.
        """
        try:
            fcntl.flock(self._lock_handle, fcntl.LOCK_UN)
        except Exception as e:
            print(str(e))
            return False
        else:
            return True
        finally:
            if self._lock_handle:
                os.close(self._lock_handle)
            self._lock_handle = None










if __name__ == '__main__':

    here       = os.getcwd()
    progname   = os.path.basename(__file__)[:-3]
    configfile = f"{here}/{progname}.toml"
    logfile    = f"{here}/{progname}.log"
    lockfile   = f"{here}/{progname}.lock"
    
    parser = argparse.ArgumentParser(prog="fname", 
        description="What fname does, fname does best.")

    parser.add_argument('--loglevel', type=int, 
        choices=range(logging.FATAL, logging.NOTSET, -10),
        default=logging.DEBUG,
        help=f"Logging level, defaults to {logging.DEBUG}")

    parser.add_argument('-o', '--output', type=str, default="",
        help="Output file name")
    
    parser.add_argument('-z', '--zap', action='store_true', 
        help="Remove old log file and create a new one.")

    myargs = parser.parse_args()
    logger = URLogger(logfile=logfile, level=myargs.loglevel)

    try:
        outfile = sys.stdout if not myargs.output else open(myargs.output, 'w')
        with contextlib.redirect_stdout(outfile):
            sys.exit(globals()[f"{progname}_main"](myargs))

    except Exception as e:
        print(f"Escaped or re-raised exception: {e}")

