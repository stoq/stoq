# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008-2012 Async Open Source <http://www.async.com.br>
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
"""Dialog for listing payment categories"""

import random

from kiwi.datatypes import ValidationError

from stoqlib.api import api
from stoqlib.domain.payment.category import PaymentCategory
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

_TANGO_PALETTE = [
    '#eeeeec',
    '#d3d7cf',
    '#babdb6',
    '#fce94f',
    '#edd400',
    '#c4a000',
    '#8ae234',
    '#73d216',
    '#4e9a06',
    '#fcaf3e',
    '#f57900',
    '#ce5c00',
    '#e9b96e',
    '#c17d11',
    '#8f5902',
    '#729fcf',
    '#3465a4',
    '#204a87',
    '#ad7fa8',
    '#75507b',
    '#5c3566',
    '#888a85',
    '#555753',
    '#2e3436',
    '#ef2929',
    '#cc0000',
    '#a40000',
    ]


class PaymentCategoryEditor(BaseEditor):
    model_name = _('Payment Category')
    model_type = PaymentCategory
    gladefile = 'PaymentCategoryEditor'
    confirm_widgets = ['name']

    def __init__(self, conn, model=None,
                 category_type=None):
        self._category_type = category_type or PaymentCategory.TYPE_PAYABLE
        BaseEditor.__init__(self, conn, model)
        if category_type is not None:
            self.category_type.set_sensitive(False)

    def create_model(self, trans):
        used_colors = set([
            pc.color for pc in PaymentCategory.select(connection=trans)])
        random.shuffle(_TANGO_PALETTE)
        for color in _TANGO_PALETTE:
            if not color in used_colors:
                break
        return PaymentCategory(name='',
                               color=color,
                               category_type=int(self._category_type),
                               connection=trans)

    def setup_proxies(self):
        self.name.grab_focus()
        self.category_type.prefill([
            (_('Payable'), PaymentCategory.TYPE_PAYABLE),
            (_('Receivable'), PaymentCategory.TYPE_RECEIVABLE)])
        self.add_proxy(self.model, ['name', 'color', 'category_type'])

    #
    # Kiwi Callbacks
    #

    def on_name__validate(self, widget, new_name):
        if not new_name:
            return ValidationError(
                _(u"The payment category should have name."))
        if self.model.check_unique_value_exists('name', new_name):
            return ValidationError(
                _(u"The payment category '%s' already exists.") % new_name)


def test():
    creator = api.prepare_test()
    retval = run_dialog(PaymentCategoryEditor, None, creator.trans, None)
    api.finish_transaction(creator.trans, retval)


if __name__ == '__main__':
    test()
