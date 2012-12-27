# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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


from stoqlib.domain.production import ProductionOrder
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.slaves.productionslave import ProductionMaterialListSlave
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class StartProductionDialog(BaseEditor):
    model_name = _(u'Production')
    model_type = ProductionOrder
    title = _(u'Start Production')
    gladefile = 'BaseTemplate'
    size = (750, 450)

    def __init__(self, store, model):
        BaseEditor.__init__(self, store, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self.enable_window_controls()
        self.main_dialog.ok_button.set_label(_(u'_Start Production'))

    #
    # BaseEditor
    #

    def setup_slaves(self):
        self._slave = ProductionMaterialListSlave(self.store, self.model, False)
        self.attach_slave('main_holder', self._slave)
