# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
"""Editors for fiscal objects"""

import collections

from kiwi.datatypes import ValidationError
from kiwi.ui.forms import TextField

from stoqlib.api import api
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.validators import validate_cfop
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.domain.fiscal import CfopData, FiscalBookEntry

_ = stoqlib_gettext


class CfopEditor(BaseEditor):
    model_name = _('C.F.O.P.')
    model_type = CfopData

    @cached_property()
    def fields(self):
        return collections.OrderedDict(
            code=TextField(_('C.F.O.P.'), input_mask="0.000", mandatory=True,
                           proxy=True),
            description=TextField(_('Description'), mandatory=True, proxy=True),
        )

    def __init__(self, store, model=None, visual_mode=False):
        BaseEditor.__init__(self, store, model, visual_mode)
        self.set_description(self.model.code)

    #
    # BaseEditor Hooks
    #

    def create_model(self, store):
        return CfopData(code=u"", description=u"",
                        store=store)

    #
    # Kiwi handlers
    #

    def on_code__validate(self, widget, value):
        if not validate_cfop(value):
            return ValidationError(_(u"'%s' is not a valid C.F.O.P. code.")
                                   % value)


class FiscalBookEntryEditor(BaseEditor):
    model_type = FiscalBookEntry
    gladefile = 'FiscalBookEntryEditor'
    proxy_widgets = ('cfop',
                     'date',
                     'invoice_number')

    def _setup_widgets(self):
        cfop_items = [(item.get_description(), item)
                      for item in self.store.find(CfopData)]
        self.cfop.prefill(cfop_items)

    #
    # BaseEditor Hooks
    #

    def get_title(self, model):
        # FIXME: bug 5531
        return _("Edit Fiscal Book Entry #%d") % (model.invoice_number or 0)

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model,
                       FiscalBookEntryEditor.proxy_widgets)

if __name__ == '__main__':  # pragma nocover
    ec = api.prepare_test()
    cfop = ec.create_cfop_data()
    run_dialog(CfopEditor, parent=None, store=ec.trans, model=cfop)
