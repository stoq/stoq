# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" A simple slave implementation for price entry/show"""

from kiwi.ui.delegates import GladeSlaveDelegate


class PriceSlave(GladeSlaveDelegate):
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
        GladeSlaveDelegate.__init__(self, toplevel_name=toplevel_name,
                                    gladefile=gladefile)
        self._proxy = None

    def set_model(self, model):
        if self._proxy is None:
            self._proxy = self.add_proxy(model, ("price", ))
        else:
            self._proxy.set_model(model)

    def get_widget(self):
        return self.price

    def update(self):
        self._proxy.update("price")
