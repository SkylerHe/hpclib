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
import datetime

###
# From hpclib
###
from   dorunrun import dorunrun
from   fname import Fname
import linuxutils
import setutils
from   sloppytree import SloppyTree
from   urdecorators import trap

###
# Objects
###

queries = SloppyTree()

queries.by_job = lambda x : f"sudo -u slurm scontrol show job {x}"
queries.all_job_ids = lambda : "sudo -u slurm squeue --format=%A"

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

    days = h // 24
    h -= days * 24
    hours = int(h)
    h -= hours
    seconds = int(h*60)

    return ( f"{days}-{hours:02}:{minutes:02}:{seconds:02}" 
        if days else
        f"{hours:02}:{minutes:02}:{seconds:02}" )


def load_avg(node:str='') -> tuple:
    """
    Get the current usage of a node.
    """
    try:
        node = int(node)
        command=f"ssh spdr{node:02} 'cat /proc/loadavg'"
    except:
        command='cat /proc/loadavg'

    result = SloppyTree(dorunrun(command, return_datatype=dict))
    if not result.OK: return None
    result = result.stdout.strip().split()
    data = [ float(_) for _ in result[:-2] ]
    data.append(int(result[-2].split('/')[0]))
    return tuple(data)

    
def node_busy(node:object) -> bool:
    try:
        node = int(node)
    except:
        return None

    command=f"scontrol show nodes spdr{node:02}"
    result = SloppyTree(dorunrun(command, return_datatype=dict))
    if not result.OK: return None
    result = parse_slurm_data(result.stdout)
    return not not int(result.CPUAlloc)


def node_powerstatus(node:object) -> Union[int,tuple]:
    """
    Inquire about the status of the node.

    node -- a node number, or a list of node numbers. 

    returns --  Returns 1 if the node is running, 0 if it is not.
        and None if the arguments were bad. If you only ask
        about one node, it returns a scalar rather than a list
        with only one value.
    """
    command = lambda node : f"sudo cv-power -n spdr{node:02} status"

    nodes = [node] if isinstance(node, (str, int)) else node
    try:
        nodes = tuple( int(node) for node in nodes )
    except Exception as e:
        return None

    results = []
    for node in nodes:
        result = SloppyTree(dorunrun(command(node), return_datatype=dict))
        if not result.OK: 
            results.append(None)
            continue

        text = next(reversed(result.stdout.split(':')))
        results.append(1 if 'on' in text else 0)        

    return results[0] if len(results) == 1 else results 


def node_start(node:Union[int,str]) -> bool:
    """
    Start a node that is currently stopped. 

    node -- a node number. 

    returns --  True if it was stopped and is now started.
                False if it was stopped and this command did not work.
                None if you asked to start a node that is already running.
    """
    if node_powerstatus(node) in (None, 1): return None
    command = f"sudo cv-power -n spdr{node:02} on"
    return dorunrun(command)


def node_stop(node:Union[int,str]) -> bool:
    """
    Stop a node that is currently running. 

    node -- a node number. 

    returns --  True if it was running and is now stopped.
                False if it was running and this command did not work.
                None if you asked to start a node that is already running.
    """
    if node_powerstatus(node) in (None, 0): return None
    command = f"sudo cv-power -n spdr{node:02} off"
    return dorunrun(command)


def parse_sinfo(params:SloppyTree=None) -> SloppyTree:
    """
    Query the current environment to get the description of the
    cluster. Return it as a SloppyTree.
    """
    if params is None:
        params = SloppyTree()
        params.querytool.opts = '-o "%50P %10c  %10m  %25f  %20G %l"'
        params.querytool.exe = dorunrun("which sinfo", return_datatype=str).strip()
        if not params.querytool.exe:
            sys.stderr.write('SLURM does not appear to be on this machine.')
            sys.exit(os.EX_SOFTWARE)
        

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
    users = dict(zip(partitions, ( setutils.Universal() for _ in partitions ) ))


    for k, v in cores.items(): tree[k].cores = int(v)
    for k, v in memories.items():
        v = "".join(_ for _ in v if _.isdigit())
        tree[k].ram = int(int(v)/1000)
    for k, v in xtras.items(): tree[k].xtras = v if 'null' not in v.lower() else None
    for k, v in gpus.items(): tree[k].gpus = v if 'null' not in v.lower() else None
    for k, v in times.items(): tree[k].max_hours = 24*365 if v == 'infinite' else hms_to_hours(v)
    for k, v in users.items(): tree[k].users = v

    return tree


@trap
def parse_slurm_data(text:str) -> SloppyTree:
    """
    Take one of the blobs that comes back from scontrol requests,
    and try to make some sense of it. The results are formatted
    for human readability, and that gets in the way of programmatic
    understanding.
    """
    result = {}
    lines = [ line for line in text.split('\n') if line ]
    for line in lines:
        eq_signs = line.count('=')
        if eq_signs == 0:
            continue

        elif eq_signs == 1:
            k, v = line.split('=')
            result[k.strip()] = linuxutils.coerce(v.strip())
            continue

        else:
            stmts = line.split()
            for stmt in stmts:
                try:
                    k, v = stmt.split('=')
                    result[k.strip()] = linuxutils.coerce(v.strip())
                except:
                    pass

    return SloppyTree(result)


def stat(jobid:Union[int,str]) -> SloppyTree:
    """
    Just like stat on files, this function will return all
    the info about a SLURM job. To the extent practical, it 
    transforms the character data into Python types.
    """
    tree = SloppyTree()
    for i, element in enumerate(
        dorunrun(queries.by_job(jobid),
                return_datatype=str).split()
                ):
        try:
            k, v = element.split('=')
            tree[k.strip().lower()] = v.strip()
        except:
            tree[f'unknown{i}'] = element
        
    # Unfortunately, the data values are all of type str, which
    # is rather limiting.
    for k, v in tree.items():
        if v in ( 'N/A', '(null)', '' ):
            tree[k] = None
            continue

        if k in ( 'userid', 'groupid' ):
            try:
                v = v.replace('(',' ').replace(')',' ').strip().split()
                tree[k] = SloppyTree({'name': v[0], 'id': v[1]})
                continue
            except:
                pass

        try:
            tree[k] = int(v); continue
        except:
            pass

        try:
            tree[k] = datetime.datetime.fromisoformat(v); continue
        except:
            pass

        try:
            x = linuxutils.byte_size(v)
            tree[k] = x if x else v
            continue
        except:
            pass


    return tree


def stat_all() -> Dict[int, SloppyTree]:
    
    jobs = queries.all_job_ids

    return { _: stat(_) 
        for _ in dorunrun(queries.all_job_ids(), 
            return_datatype=str).split('\n')[1:] }           
    
