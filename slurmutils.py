# -*- coding: utf-8 -*-
"""
Slurm utilities.
"""
import typing
from   typing import *

min_py = (3, 8)

###
# Standard imports, starting with os and sys
###
import os
import sys
if sys.version_info < min_py:
    print(f"This program requires Python {min_py[0]}.{min_py[1]}, or higher.")
    sys.exit(os.EX_SOFTWARE)

###
# Other standard distro imports
###
import argparse
import dateparser
import datetime
import fnmatch
import getpass
import grp
import math
import pwd
import socket
import stat
import subprocess

###
# From hpclib
###
from   dorunrun import dorunrun
from   fname import Fname
import linuxutils
from   sloppytree import SloppyTree

###
# Credits
###
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2021'
__credits__ = None
__version__ = 0.1
__maintainer__ = 'George Flanagin'
__email__ = ['me@georgeflanagin.com', 'gflanagin@richmond.edu']
__status__ = 'in progress'
__license__ = 'MIT'


def get_jobname(s:str) -> str:
    """
    Wrap this up in case we need to universally change the way it is done.
    """
    jobname = Fname(s).fname_only
    return f"q_{jobname}" if jobname[0].isdigit() else jobname


def hms_to_hours(hms:str) -> float:
    """
    Convert a slurm time like 2-12:00:00 to
    a number of hours.
    """

    try:
        h, m, s = hms.split(':')
    except Exception as e:
        if hms == 'infinite': return 365*24
        return 0

    try:
        d, h = h.split('-')
    except Exception as e:
        d = 0

    return int(d)*24 + int(h) + int(m)/60 + int(s)/3600


def hours_to_hms(h:float) -> str:
    """
    Convert a number of hours to "SLURM time."
    """

    days = int(h / 24)
    h -= days * 24
    hours = int(h)
    h -= hours
    minutes = int(h * 60)
    h -= minutes/60
    seconds = int(h*60)

    return ( f"{hours:02}:{minutes:02}:{seconds:02}"
        if h < 24 else
        f"{days}-{hours:02}:{minutes:02}:{seconds:02}" )


def parse_sinfo(params:SloppyTree) -> SloppyTree:
    """
    Query the current environment to get the description of the
    cluster. Return it as a SloppyTree.
    """

    # These options give us information about cpus, memory, and
    # gpus on the partitions. The first line of the output
    # is just headers.
    cmdline = f"{params.querytool.exe} {params.querytool.opts}"
    result = dorunrun( cmdline, return_datatype=str).split('\n')[1:]

    partitions = []
    cores = []
    memories = []
    xtras = []
    gpus = []
    times = []
    tree = SloppyTree()

    # Ignore any blank lines.
    for line in ( _ for _ in result if _):
        f1, f2, f3, f4, f5, f6 = line.split()
        if f1.endswith('*'):
            f1=f1[:-1]
            tree.default_partition=f1
        partitions.append(f1)
        cores.append(f2)
        memories.append(f3)
        xtras.append(f4)
        gpus.append(f5)
        times.append(f6)

    cores = dict(zip(partitions, cores))
    memories = dict(zip(partitions, memories))
    xtras = dict(zip(partitions, xtras))
    gpus = dict(zip(partitions, gpus))
    times = dict(zip(partitions, times))

    for k, v in cores.items(): tree[k].cores = int(v)
    for k, v in memories.items():
        v = "".join(_ for _ in v if _.isdigit())
        tree[k].ram = int(int(v)/1000)
    for k, v in xtras.items(): tree[k].xtras = v if 'null' not in v.lower() else None
    for k, v in gpus.items(): tree[k].gpus = v if 'null' not in v.lower() else None
    for k, v in times.items(): tree[k].max_hours = 24*365 if v == 'infinite' else hms_to_hours(v)

    return tree


