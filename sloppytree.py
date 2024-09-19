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
from functools import reduce
###
# From hpclib
###
import linuxutils
from   urdecorators import trap
from   urlogger import URLogger

###
# imports and objects that were written for this project.
###
import curses
import enum 
import math
import pprint
###
# Global objects
###
mynetid = getpass.getuser()
logger = None
T, L, I, H = "├", "└", "┃", "─"
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


###
# Indicator(enum.IntEnum)
###
class Indicator(enum.IntEnum):
    KEY = 1
    LEAF = 0

# SloppyException
###
class SloppyException(LookupError):
    def __init__(self, message, original_exception=None):
        super().__init__(message)
        self.original_exception = original_exception

    def raise_original(self):
        """Re-raise the orignal exception if it exists"""
        if self.original_exception:
            raise self.original_exception
        else:
            raise self 




class SloppyDict: pass
###
# Utility functions
###
def deepsloppy(o:dict) -> Union[SloppyDict, object]:
    """
    Multi level slop.
    """
    if isinstance(o, dict):
        o = SloppyTree(o)
        for k, v in o.items():
            o[k] = deepsloppy(v)

    elif isinstance(o, list):
        for i, _ in enumerate(o):
            o[i] = deepsloppy(_)

    else:
        pass

    return o

def sloppy(o:object) -> SloppyDict:
    """
    Returns a dictionary.
    """
    return o if isinstance(o, SloppyDict) else SloppyDict(o)

###
# SloppyDict
###
class SloppyDict(dict):
    """
    Make a dict into an object for notational convenience.
    """
    ###
    # Magic methods
    ###
    def __delattr__(self, k:str) -> None:
        """
        Deletes the key in the dictionary.
        """
        if k in self: del self[k]
        else: raise SloppyException(f"No element named {k}")
    
    def __getattr__(self, k:str) -> object:
        """
        Gets the value of the key in the dictionary.
        """
        if k in self: return self[k]
        raise SloppyException(f"No element named {k}")

    def __setattr__(self, k:str, v:object) -> None:
        """
        Assign the value as expected.
        """
        self[k] = v


    ###
    # Regular methods
    ###
    def reorder(self, some_keys:list=[], self_assign:bool=True) -> SloppyDict:
        """
        Sorts the keys in the dictionary.
        """
        new_data = SloppyDict()
        unmoved_keys = sorted(list(self.keys()))

        for k in some_keys:
            try:
                new_data[k] = self[k]
                unmoved_keys.remove(k)
            except KeyError as e:
                raise SloppyException(f"{k} not found")
        
        for k in unmoved_keys:
            new_data[k] = self[k]

        if self_assign:
            self = new_data
            return self
        else:
            return new_data

    

class SloppyTree: pass
class SloppyTree(dict):
    """
    Like SloppyDict() only worse -- much worse.
    """
    ###
    # Magic methods
    ###
    ###
    # A
    ###
    ###
    # B
    ###
    def __bool__(self) -> bool:
        """
        When a SloppyTree is evaluated with if, it becomes a boolean.
        Let's avoid any use of the tree's iterators, and just answer
        the question, "Is this tree empty?"
        """
        return not not len(self.items())


    ###
    # C
    ###
    def __call__(self, key_as_str:str) -> object:
        """
        Allow for retrieval of a nested key by a string
        that represents its name. Essentially this:

        t("a.b.c") means t[a][b][c]
        """
        ptr = self
        for k in key_as_str.split('.'):
            if k not in ptr:
                raise SloppyException(f"{k=} not found in sub-tree {ptr=}")
            ptr = v = ptr[k]
        return v


    ###
    # D
    ###
    def __delattr__(self, k:str) -> None:
        """
        Remove it if we can.
        """
        if k in self: del self[k]

    ###
    # E,F
    ###
    ###
    # G
    ###
    def __getattr__(self, k:str) -> object:
        """
        Retrieve the element, or implicity call the over-ridden
        __missing__ method, and make a new one.
        """
        return self[k]


    def __getstate__(self): return self.__dict__


    ###
    # H,I,J,K
    ###

    ###
    # L
    ###
    def __len__(self) -> int:

        """
        return the number of nodes/branches.
        """
        return sum(1 for _ in (i for i in self.traverse(False)))

    ###
    # M
    ###
    def __missing__(self, k:str) -> object:
        """
        If we reference an element that doesn't exist, we create it,
        and assign a SloppyTree to its value.
        """
        self[k] = SloppyTree()
        return self[k]

    ###
    # N,O,P,Q
    ###
    ###
    # I
    ###
    def __invert__(self) -> int:
        """
        return the number of paths from the root node to the leaves,
        ignoring the nodes along the way.
        """
        return sum(1 for _ in (i for i in self.leaves()))


    def __iter__(self) -> object:
        """
        NOTE: dict.__iter__ only sees keys, but SloppyTree.__iter__
        also sees the leaves.
        """
        return self.traverse()
    
    ###
    # S 
    ###
    def __setattr__(self, k:str, v:object) -> None:
        """
        Sets the value to the key, or iterated key. This syntax:

            d[(1, 'c', 6)] = 'value'

        is the same as:

            d[1]['c'][6] = 'value'
        """
        # Typical case, k is the key we want.
        if isinstance(k, str):
            self[k] = v

        elif len(k) == 1:
            self[k[0]] = v

        else:
            for element in k:
                d = self[element]
                d[k[1:]] = v


    def __setitem__(self, k:str, v:object) -> None:
        """
        Sets the value to the key, or iterated key. This syntax:

            d[(1, 'c', 6)] = 'value'

        is the same as:
 
            d[1]['c'][6] = 'value'
        """
        # Typical case, k is the key we want.
        if isinstance(k, (str, int)):
            super().__setitem__(k, v)
            return

        elif isinstance(k, (list, tuple)):
            if len(k) == 1:
                self[k[0]] = v
                return
            elif len(k) > 1:
                self[k[0]][k[1:]] = v
                return

        else:
            sys.exit(1)


    def __setstate__(self, d): self.__dict__.update(d)
    
    def __str__(self) -> str:
        return self.printable


        

    ###
    # Regular methods 
    ###

    ###
    ###
    # A
    ###
    def as_tuples(self) -> tuple:
        """
        A generator to return all paths from root to leaves as
        tuples of the nodes along the way.
        """
        tup = []
        for node, indicator in self.traverse():
            tup.append(node)
            if not indicator:
                yield tuple(tup)
                tup = []
    ###
    # B,C,D,E,F,G,H,I,J,K
    ###


    ###
    # L
    ###
    def leaves(self) -> object:
        """
        Walk the leaves only, left to right.
        """
        for k, v in self.items():
            if isinstance(v, dict):
                if v=={}:
                    yield v
                yield from SloppyTree(v).leaves()
            else:
                yield v
    
    ###
    # M,N,O
    ###
    ###
    # P
    ###
    def printable(self) -> str:
        """
        Printing one of these things requires a bit of finesse.
        """
        return pprint.pformat(dict(self), compact=True, sort_dicts=True, indent=4, width=100)

    ###
    # Q,I
    ###
    ###
    # S
    ###
    def traverse(self, with_indicator:bool=True) -> Union[Tuple[object, int], object]:
        """
        Emit all the nodes of a tree left-to-right and top-to-bottom.
        The bool is included so that you can know whether you have reached
        a leaf.

        returns -- a tuple with the value of the node, and 1 => key, and 0 => leaf.

        Usages:
            for node, indicator in mytree.traverse(): ....
            for node in mytree.traverse(with_indicator=False): ....
                ....
        """

        for k, v in self.items():
            yield k, Indicator.KEY if with_indicator else k
            if isinstance(v, dict):
                yield from SloppyTree(v).traverse(with_indicator)
            else:
                yield v, Indicator.LEAF if with_indicator else v


    def tree_as_table(self, nested_dict:SloppyTree=None, prepath=()):
        """
        Finds the path from the root to each leaf.
        """
        if nested_dict is None: nested_dict = self
        for k, v in nested_dict.items():
            path = prepath + (k,)
            #print("the path is here ", path)
            if isinstance(v, dict): # v is a dict
                if v=={}:
                    yield path
                else:
                    yield from self.tree_as_table(v, path)
            else:
                #### append the value of the leaf based on the key here
                path=path+(nested_dict.get(k), )
                yield path



    def display_tree(self,stdscr, prefix="", depth=0):
        """
        Display the SloppyTree structure with indentation represnting the tree hierarchy
        """

        curses.start_color()
        
        # Define color pairs
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)  # For root nodes
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # For leaf nodes
        
        root_color = curses.color_pair(1)
        leaf_color = curses.color_pair(2)
        default_color = curses.A_NORMAL  # Default color for branches

        for i, (k, v) in enumerate(self.items()):
            # Determine if this is the root node or a leaf node
            is_leaf = not isinstance(v, (dict, list))
            color = root_color if depth == 0 else (leaf_color if is_leaf else default_color)
            
            # Determine the appropriate line connector
            is_last = i == len(self) - 1
            connector = L if is_last else T
            stdscr.addstr(depth, 0, prefix + f"{connector}{H}{H} " + str(k), color)
            
            # Prepare new prefix for child nodes
            new_prefix = prefix + ("    " if is_last else f"{I}   ")
            depth += 1
            
            # Recursively handle nested structures
            if isinstance(v, dict):
                depth = SloppyTree(v).display_tree(stdscr, new_prefix, depth)
            elif isinstance(v, list):
                for idx, item in enumerate(v):
                    is_last_item = idx == len(v) - 1
                    item_connector = L if is_last_item else T
                    item_prefix = new_prefix + ("    " if is_last_item else f"{I}   ")
                    
                    if isinstance(item, dict):
                        depth = SloppyTree(item).display_tree(stdscr, item_prefix, depth)
                    else:
                        stdscr.addstr(depth, 0, item_prefix + f"{item_connector}{H}{H} " + str(item), leaf_color)
                        depth += 1
            else:
                stdscr.addstr(depth, 0, new_prefix + f"{L}{H}{H} " + str(v), leaf_color)
                depth += 1

        return depth

