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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##


import difflib
import os
import re


def _diff(orig, new, short, verbose):
    lines = difflib.unified_diff(orig, new)
    if not lines:
        return ''

    return ''.join('%s %s' % (short, line) for line in lines)


def diff_files(orig, new, verbose=False):
    """Diff two files.

    @return: True i the files differ otherwise False
    :rtype: bool
    """
    with open(orig) as f_orig:
        with open(new) as f_new:
            return _diff(f_orig.readlines(),
                         f_new.readlines(),
                         short=os.path.basename(orig),
                         verbose=verbose)


def diff_lines(orig_lines, new_lines, short='<stdin>', verbose=False):
    """Diff two files.

    @return: True i the files differ otherwise False
    :rtype: bool
    """
    return _diff(orig_lines,
                 new_lines,
                 short=short,
                 verbose=verbose)


def diff_strings(orig, new, short='<input>', verbose=False):
    """Diff two strings.

    @return: True i the files differ otherwise False
    :rtype: bool
    """
    def _tolines(s):
        return [s + '\n' for line in s.split('\n')]

    return _diff(_tolines(orig),
                 _tolines(new),
                 short=short,
                 verbose=verbose)


def diff_pdf_htmls(original_filename, filename):
    for fname in [original_filename, filename]:
        with open(fname) as f:
            data = f.read()
            # REPLACE all generated dates with %%DATE%%
            data = re.sub(r'name="date" content="(.*)"',
                          r'name="date" content="%%DATE%%"', data)
            # Remove poppler identifier and version
            data = re.sub(r'<pdf2xml(.*)>',
                          r'<pdf2xml>', data)
        with open(fname, 'w') as f:
            f.write(data)

    return diff_files(original_filename, filename)
