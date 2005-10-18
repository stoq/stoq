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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
##  Author(s): Evandro Vale Miquelito   <evandro@async.com.br>
##
"""
stoq/gui/slaves/status.py:

    Slaves for status management
"""

import gettext

import gobject
from kiwi.ui.delegates import SlaveDelegate
from kiwi.utils import gsignal

_ = gettext.gettext


class StatusSlave(SlaveDelegate):
    """A generic slave for statuses management useful when combined with
    SearchBar as a filter_slave.
    
    statuses    = a list of tuples where each item has this format:
                  (string, data). This tuple will be used when filling the
                  statuses-combo
    selected    = the data we want to select in the combo. This argument
                  must be one of the elements in the position 1 (one) of
                  statuses tuple argument.
    """

    gladefile = 'StatusSlave'
    
    widgets = ('statuses_combo',)
    gsignal('status-changed')

    def __init__(self, statuses, selected=None):
        SlaveDelegate.__init__(self, gladefile=self.gladefile, 
                               widgets=self.widgets)
        self.statuses_combo.prefill(statuses)
        if not isinstance(statuses, (tuple, list)):
            raise TypeError('Argument statuses must be of typle list or '
                            'tuple, got %s instead' % type(statuses))
        if not len(statuses):
            raise ValueError('Argument statuses must have at least one '
                             'item, found zero.')
        selected = selected or statuses[0]
        self.statuses_combo.select_item_by_data(selected)

    def get_selected_status(self):
        return self.statuses_combo.get_selected_data()



    #
    # Kiwi callbacks
    #



    def on_statuses_combo__content_changed(self, *args):
        self.emit('status-changed')

gobject.type_register(StatusSlave)
