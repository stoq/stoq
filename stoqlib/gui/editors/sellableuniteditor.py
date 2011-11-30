# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
##
""" Implementation of SellableUnit editor """


from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.domain.sellable import SellableUnit
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

#
#  Editors
#


class SellableUnitEditor(BaseEditor):
    """An editor for L{stoqlib.domain.sellable.SellableUnit}"""

    gladefile = 'SellableUnitEditor'
    model_type = SellableUnit
    model_name = _('Product Unit')
    proxy_widgets = ('description',
                     'allow_fraction')

    #
    #  BaseEditor Hooks
    #

    def create_model(self, conn):
        return SellableUnit(connection=conn, description=u'')

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model,
                                    SellableUnitEditor.proxy_widgets)
