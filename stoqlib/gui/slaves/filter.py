# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
##  Author(s): Evandro Vale Miquelito   <evandro@async.com.br>
##
""" Useful slaves for filtering data in SearchBar """

import gettext

from kiwi.ui.delegates import SlaveDelegate
from kiwi.utils import gsignal

_ = gettext.gettext


class FilterSlave(SlaveDelegate):
    """A generic slave for statuses management useful when combined with
    SearchBar as a filter_slave.
    
    statuses    = a list of tuples where each item has this format:
                  (string, data). This tuple will be used when filling the
                  statuses-combo
    selected    = the data we want to select in the combo. This argument
                  must be one of the elements in the position 1 (one) of
                  statuses tuple argument.
    """
    gladefile = 'FilterSlave'
    gsignal('status-changed')


    def __init__(self, statuses, selected=None):
        SlaveDelegate.__init__(self, gladefile=self.gladefile, 
                               widgets=self.widgets)
        if not isinstance(statuses, (tuple, list)):
            raise TypeError('Argument statuses must be of typle list or '
                            'tuple, got %s instead' % type(statuses))
        if not len(statuses):
            raise ValueError('Argument statuses must have at least one '
                             'item, found zero.')
        self.filter_combo.prefill(statuses)
        if len(statuses) == 1:
            self.filter_combo.set_sensitive(False)
        if selected is None:
            selected = statuses[0][0]
        self.filter_combo.select_item_by_data(selected)

    def get_selected_status(self):
        return self.filter_combo.get_selected_data()

    def set_filter_label(self, text):
        self.filter_label.set_text(text)


    #
    # Kiwi callbacks
    #

    def on_filter_combo__content_changed(self, *args):
        self.emit('status-changed')
