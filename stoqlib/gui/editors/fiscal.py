# -*- coding: utf-8 -*-
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##
##
"""Editors for fiscal objects"""


from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.editors import BaseEditor
from stoqlib.domain.fiscal import CfopData

_ = stoqlib_gettext

class CfopEditor(BaseEditor):
    model_name = _('CFOP')
    model_type = CfopData
    gladefile = 'CfopEditor'
    proxy_widgets = ('code', 'description')

    #
    # BaseEditor Hooks
    #

    def get_title_model_attribute(self, model):
        return model.code

    def create_model(self, conn):
        return CfopData(code=u"", description=u"",
                        connection=conn)

    def setup_proxies(self):
        self.add_proxy(self.model, CfopEditor.proxy_widgets)
