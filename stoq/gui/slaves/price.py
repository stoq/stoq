# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Henrique Romano             <henrique@async.com.br>
##
"""
gui/slaves/price.py:

        A simple slave implementation for price entry/show.
"""

from kiwi.ui.delegates import SlaveDelegate

from stoqlib.lib.validators import get_price_format_str

class PriceSlave(SlaveDelegate):
    """ A simple slave that show a price with a label (when can_edit
    parameter is False) or a entry (can_edit is True).  It is necessary
    that the model has a 'price' attribute
    """
    def __init__(self, can_edit=False):
        if can_edit:
            gladefile = "PriceEntrySlave"
        else:
            gladefile = "PriceLabelSlave"
        toplevel_name = gladefile
        SlaveDelegate.__init__(self, toplevel_name, gladefile=gladefile)
        self.price.set_data_format(get_price_format_str())
        self._proxy = None

    def set_model(self, model):
        if self._proxy is None:
            self._proxy = self.add_proxy(model, ("price",))
        else:
            self._proxy.new_model(model)

    def get_widget(self):
        return self.price

    def update(self):
        self._proxy.update("price")
