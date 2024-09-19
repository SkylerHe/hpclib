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

###
# From hpclib
###
import linuxutils
from   urdecorators import trap
from   urlogger import URLogger

###
# imports and objects that were written for this project.
###
import base64
import calendar
import fcntl
import fnmatch
import getpass
import glob
import pickle
import random
import re
import resource
import stat
import subprocess
import sys
import tempfile

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
__email__ = 'gflanagin@richmond.edu, skyler.he@richmond.edu'
__status__ = 'in progress'
__license__ = 'MIT'



####
# A
####
def all_dirs_in(s:str, depth:int=0) -> str:
    """
    A generator to get the names of directories under the
    one given as the first parameter.
    """
    s = expandall(s)
    if depth==1:
        return next(os.walk(s))[1]
    else:
        return [t[0] for t in os.walk(s)]


def all_files_in(s:str, include_hidden:bool=False) -> str:
    """
    A generator to cough up the full file names for every
    file in a directory.
    """
    s = expandall(s)
    for c, d, files in os.walk(s):
        for f in files:
            s = os.path.join(c, f)
            if not include_hidden and is_hidden(s): continue
            yield s


def all_files_like(d:str, partial_name:str) -> str:
    """
    A list of all files that match the argument
    """
    yield from ( f for f in all_files_in(d) if partial_name in f )


def all_files_not_like(d:str, partial_name:str) -> str:
    """
    A list of all files that do not match the argument
    """
    yield from ( f for f in all_files_in(d) if partial_name not in f )


def all_module_files() -> str:
    """
    This generator locates all module files that are located in
    the directories that are members of MODULEPATH.
    """
    for location in os.getenv('MODULEPATH', "").split(':'):
        yield from all_files_in(location)


def append_blob(b:bytes, f:Union[str, object]) -> int:
    """
    Appends b to f, and allows f to be an alread open file
    or a filename. This function does a lock on the file allowing
    for safe operation in a multi-process/thread environment.

    returns -1 on error or number of bytes written.
    """
    try:
        f = open(f, 'ab+') if isinstance(f, str) else f
        fcntl.lockf(f, fcntl.LOCK_EX)
        return f.write(b)
    except Exception as e:
        return -1
    finally:
        f.close()


def append_pickle(o:object, f:Union[str, object]) -> Union[bool, int]:
    """
    Pickles o and appends it to f.

    returns True on success, False on a failure to pickle, and
        -1 on any IO Error.
    """
    try:
        f = open(f, 'ab+') if isinstance(f, str) else f
        fcntl.lockf(f, fcntl.LOCK_EX)
        pickle.dump(o, f)
        return True
    except pickle.PicklingError as e:
        return False
    except Exception as e:
        return -1
    finally:
        f.close()


def append_text(s:str, f:Union[str, object]) -> int:
    """
    Appends s to f, and allows f to be an alread open file
    or a filename. This function does a lock on the file allowing
    for safe operation in a multi-process/thread environment.

    returns -1 on error or number of bytes written.
    """
    try:
        f = open(f, 'a+') if isinstance(f, str) else f
        fcntl.lockf(f, fcntl.LOCK_EX)
        return f.write(s)
    except Exception as e:
        return -1
    finally:
        f.close()


####
# B
####



####
# C 
####

####
# D
####

####
# E
####

def expandall(s:str) -> str:
    """
    Expand all the user vars into an absolute path name. If the
    argument happens to be None, it is OK.
    """
    return s if s is None else os.path.realpath(os.path.abspath(os.path.expandvars(os.path.expanduser(s))))


def extract_pickle(f:Union[str,object]) -> object:
    """
    A generator to read a file of pickles.
    """
    try:
        f = open(f, 'rb') if isinstance(f, str) else f
        while True:
            try:
                yield pickle.load(f)
            except EOFError:
                break
    finally:
        f.close()

####
# F
####

def fclose_all() -> None:
    for i in range (0, 1024):
        try:
            os.close(i)
        except:
            continue

####
# G
####

def get_file_page(path:str,num_bytes:int=resource.getpagesize()) -> str:
    """
    Returns the first num_bytes of a file as a tuple of hex strings

    path -- path to file
    num_bytes -- number of bytes from position 0 to return
    """
    with open(path,'rb') as z:
        return z.read(num_bytes)



filetypes = {
    b"%PDF-1." : "PDF",
    b"#%Module" : "MOD",
    b"BZh91A" : "BZ2",
    bytes.fromhex("FF454C46") : "ELF",
    bytes.fromhex("1F8B") : "GZIP",
    bytes.fromhex("FD377A585A00") : "XZ",
    bytes.fromhex("504B0304") : "ZIP",
    bytes.fromhex("504B0708") : "ZIP"
    }


def get_file_type(path:str) -> str:
    """
    By inspection, return the presumed type of the file located
    at path. Returns a three of four char file type, or None if
    the type cannot be determined. This might be because the
    type cannot be determined when inspected, or because it cannot
    be opened.
    """
    global filetypes

    try:
        with open(expandall(path), 'rb') as f:
            shred = f.read(256)
    except PermissionError as e:
        return None

    for k, v in filetypes.items():
        if shred.startswith(k): return v

    return "TXT" if shred.isascii() else None



def got_data(filenames:Iterable) -> bool:
    """
    Return True if the file or files all are non-empty, False otherwise.
    """
    if filenames is None or not len(filenames): return False

    filenames = filenames if isinstance(filenames, list) else [filenames]
    result = True
    for _ in filenames:
        result = result and bool(os.path.isfile(_)) and bool(os.stat(_).st_size)
    return result


####
# H
####
def home_and_away(filename:str) -> str:
    """
    Looks for the file in $PWD, $OLDPWD, $HOME, and then /scratch if it is
    not fully qualified. Note that this function only returns None if no
    files like filename are found in any of the locations.

    It has the benefit that unless nothing is found, it returns the
    filename fully qualified.
    """

    if filename.startswith(os.sep): return filename

    s = os.path.join(os.environ.get('PWD',''), filename)
    if os.path.exists(s): return s
    s = os.path.join(os.environ.get('OLDPWD',''), filename)
    if os.path.exists(s): return s
    s = os.path.join(os.environ.get('HOME', ''), filename)
    if os.path.exists(s): return s
    s = os.path.join(os.environ.get(f'/scratch/{getpass.getuser()}', filename))
    if os.path.exists(s): return s

    return None


####
# I
####
def is_hidden(path:str) -> bool:
    """
    returns True if the path is hidden
    """
    return True if "/." in path else False


def is_PDF(o:Union[bytes,str]) -> bool:
    """
    Determine if a file is a PDF file or something else.

    o -- as a str, it is interpreted to be a filename; if bytes,
        we assume it is the first part of some file-like data
        object.

    returns True if the file or data start with %PDF-1.
    """

    shred = None
    if isinstance(o, str):
        with open(o, "rb") as f:
            shred = f.read(7)
    else:
        shred = o[:7]
    return shred == b'%PDF-1.'


####
# J
####

####
# K
####

####
# L
####

def lines_in_file(filename:str) -> int:
    """
    Count the number of lines in a file by a consistent means.
    """
    if not os.path.isfile(filename): return 0

    try:
        count = int(subprocess.check_output([
            "/bin/grep", "-c", os.linesep, filename
            ], universal_newlines=True).strip())
    except subprocess.CalledProcessError as e:
        tombstone(str(e))
        return 0
    except ValueError as e:
        tombstone(str(e))
        return -2
    else:
        return count


####
# M
####

def make_dir_or_die(dirname:str, mode:int=0o700) -> None:
    """
    Do our best to make the given directory (and any required
    directories upstream). If we cannot, then die trying.
    """

    dirname = expandall(dirname)

    try:
        os.makedirs(dirname, mode)

    except FileExistsError as e:
        # It's already there.
        if not os.path.isdir(dirname):
            raise NotADirectoryError('{} is not a directory.'.format(dirname)) from None
            sys.exit(os.EX_IOERR)

    except PermissionError as e:
        # This is bad.
        tombstone()
        tombstone("Permissions error creating/using " + dirname)
        sys.exit(os.EX_NOPERM)

    if (os.stat(dirname).st_mode & 0o777) < mode:
        tombstone("Permissions on " + dirname + " less than requested.")



####
# N
####

####
# O
####

####
# P
####

def path_join(dir_part:str, file_part:str) -> str:
    """
    Like os.path.join(), but trapping the None-s and replacing
    them with appropriate structures.
    """
    if dir_part is None:
        tombstone("trapped a None in directory name")
        dir_part = ""

    if file_part is None:
        tombstone("trapped a None in filename")
        file_part = ""

    dir_part = os.path.expandvars(os.path.expanduser(dir_part))
    file_part = os.path.expandvars(os.path.expanduser(file_part))
    return os.path.join(dir_part, file_part)


###
# Q
###

###
# R
###

def random_file(name_prefix:str, *, length:int=None, break_on:str=None) -> tuple:
    """
    Generate a new file, with random contents, consisting of printable
    characters.

    name_prefix -- In case you want to isolate them later.
    length -- if None, then a random length <= 1MB
    break_on -- For some testing, perhaps you want a file of "lines."

    returns -- a tuple of file_name and size.
    """
    f_name = None
    num_written = -1

    file_size = length if length is not None else random.choice(range(0, 1<<20))
    s = random_string(file_size, True)

    if break_on is not None:
        if isinstance(break_on, str): break_on = break_on.encode('utf-8')
        s = s.replace(break_on, b'\n')

    try:
        f_no, f_name = tempfile.mkstemp(suffix='.txt', prefix=name_prefix)
        num_written = os.write(f_no, s)
        os.close(f_no)
    except Exception as e:
        tombstone(str(e))
    
    return f_name, num_written

def random_string(length:int=10, want_bytes:bool=False, all_alpha:bool=True) -> str:
    """
    Generates a random string or byte sequence of the specified length.

    Parameters:
    length (int): The desired length of the output string or byte sequence. Default is 10.
    want_bytes (bool): If True, returns the result as a bytes object. If False, returns a string. Default is False.
    all_alpha (bool): If True, ensures the resulting string consists only of alphabetic characters (a-z, A-Z).
                      If False, the resulting string may include non-alphabetic characters. Default is True.

    Returns:
    str: A random string of the specified length if `want_bytes` is False.
    bytes: A random byte sequence of the specified length if `want_bytes` is True.

    """

    s = base64.b64encode(os.urandom(length*2))
    if want_bytes: return s[:length]

    s = s.decode('utf-8')
    if not all_alpha: return s[:length]

    t = "".join([ _ for _ in s if _.isalpha() ])[:length]
    return t


def read_whitespace_file(filename:str, *, comment_char:str=None) -> tuple:
    """
    This is a generator that returns the whitespace delimited tokens
    in a text file, one token at a time.
    """
    if not filename: return tuple()

    if not os.path.isfile(filename):
        sys.stderr.write(f"{filename} cannot be found.")
        return os.EX_NOINPUT

    with open(filename) as f:
        if comment_char is None:
            yield from (" ".join(f.read().split('\n'))).split()
    
        else:
            lines = f.readlines()
            yield from (token for l in lines if not l.strip().startswith(comment_char) for token in l.split())
####
#S T U V W X Y Z
####
