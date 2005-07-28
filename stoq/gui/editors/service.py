# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
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
"""
stoq/gui/editors/category.py:

    Service item editor implementation
"""


from stoqlib.gui.editors import BaseEditor

from stoq.domain.service import ServiceSellableItem


class ServiceEditor(BaseEditor):
    gladefile = 'ServiceEditor'
    widgets = ('service_name_label', 
               'price', 
               'estimated_fix_date',
               'notes')
    size = (500, 250)
    title = _('Service Details')
    model_type = ServiceSellableItem

    def __init__(self, conn, model):
        if not model:
            raise TypeError('This Editor (%r) requires a valid (%s) object'
                            % (self, self.model_type.__name__))

        BaseEditor.__init__(self, conn, model)
        self.service_name_label.set_bold(True)

    def set_widgets_format(self):
        self.price.set_data_format('%.2f')

    #
    # BaseEditor hooks
    # 

    def setup_proxies(self):
        self.set_widgets_format()
        self.add_proxy(self.model, self.widgets)

