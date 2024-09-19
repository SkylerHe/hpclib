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
__maintainer__ = 'George Flanagin'
__email__ = 'gflanagin@richmond.edu'
__status__ = 'in progress'
__license__ = 'MIT'


@trap
def skel_main(myargs:argparse.Namespace) -> int:
    return os.EX_OK


if __name__ == '__main__':

    here       = os.getcwd()
    progname   = os.path.basename(__file__)[:-3]
    configfile = f"{here}/{progname}.toml"
    logfile    = f"{here}/{progname}.log"
    lockfile   = f"{here}/{progname}.lock"
    
    parser = argparse.ArgumentParser(prog="skel", 
        description="What skel does, skel does best.")

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
