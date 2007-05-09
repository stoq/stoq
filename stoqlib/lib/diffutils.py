# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##
## Author(s): Johan Dahlin <jdahlin@async.com.br>
##            Lorenzo Gil Sanchez <lgz@sicem.biz>
##


import difflib
import os

def _diff(orig, new, short, verbose):
    lines = difflib.unified_diff(orig, new)
    if not lines:
        return

    diff = False
    try:
        first = lines.next()
        diff = True
    except StopIteration:
        pass
    else:
        print
        print '%s: %s' % (short, first[:-1])
        for line in lines:
            print '%s: %s' % (short, line[:-1])

    return diff

def diff_files(orig, new, verbose=False):
    """
    Diff two files.

    @return: True i the files differ otherwise False
    @rtype: bool
    """
    return _diff(open(orig).readlines(),
                 open(new).readlines(),
                 short=os.path.basename(orig),
                 verbose=verbose)

def diff_strings(orig, new, verbose=False):
    """
    Diff two strings.

    @return: True i the files differ otherwise False
    @rtype: bool
    """
    def _tolines(s):
        return [s + '\n' for line in s.split('\n')]

    return _diff(_tolines(orig),
                 _tolines(new),
                 short='<input>',
                 verbose=verbose)
