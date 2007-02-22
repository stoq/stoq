# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Stoqdrivers
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s): Henrique Romano             <henrique@async.com.br>
##
"""
Functions for general use.
"""

import os
import unicodedata

def get_module_list(dirname):
    """ Given a directory name, returns a list of all Python modules in it
    """
    modules = []
    for entry in os.listdir(dirname):
        if (not entry.endswith(".py") or entry.startswith("__init__.py")
            or not os.path.isfile(os.path.join(dirname, entry))):
            continue
        modules.append(entry[:-3])
    return modules

def encode_text(text, encoding):
    """ Converts the string 'text' to encoding 'encoding' and optionally
    normalizes the string (currently only for ascii)

    @param text:       text to convert
    @type text:        str
    @param encoding:   encoding to use
    @type text:        str
    @returns:          converted text
    """
    if not isinstance(text, unicode):
        return text
    if encoding == "ascii":
        text = unicodedata.normalize("NFKD", text)
    return text.encode(encoding, "ignore")
