# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##
"""
stoq/gui/pos/app.py:

    Main callsite for POS application
"""

import gettext

from stoqlib.database.runtime import get_connection
from stoqlib.domain.till import Till
from stoqlib.lib.message import error
from stoqlib.lib.parameters import sysparam

from stoq.gui.pos.pos import POSApp

_ = gettext.gettext

# Here we define config in the call site: /bin/stoq file
def main(config):
    conn = get_connection()
    param = sysparam(conn)
    if (param.POS_SEPARATE_CASHIER and
        not Till.get_current(conn)):
        error(_(u"You need to open the till before start doing sales."))

    return POSApp
