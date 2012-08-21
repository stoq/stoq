# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

import locale

from kiwi.python import namedAny

from stoqlib.lib.cardinals import generic


def get_cardinal_module():
    lang = locale.getlocale()[0]
    if not lang:
        # For tests
        return generic

    # First try the full LANG, like 'pt_BR', 'en_US', etc
    path = 'stoqlib.lib.cardinals.%s' % (lang, )
    try:
        return namedAny(path)
    except (ImportError, AttributeError):
        # Then base lang, 'pt', 'en', etc
        base_lang = lang[:2]
        path = 'stoqlib.lib.cardinals.%s' % (base_lang, )
        try:
            return namedAny(path)
        except (ImportError, AttributeError):
            return generic


def get_cardinal_function(func_name):
    module = get_cardinal_module()
    function = getattr(module, func_name, None)

    if not function:
        function = getattr(generic, func_name)

    assert function
    assert callable(function)

    return function
