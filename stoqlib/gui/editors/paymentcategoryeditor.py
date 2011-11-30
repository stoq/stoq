# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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

from kiwi.datatypes import ValidationError

from stoqlib.domain.payment.category import PaymentCategory
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class PaymentCategoryEditor(BaseEditor):
    model_name = _('Payment Category')
    model_type = PaymentCategory
    gladefile = 'PaymentCategoryEditor'
    confirm_widgets = ['name']

    def create_model(self, trans):
        return PaymentCategory(name='',
                               color='#000000',
                               connection=trans)

    def setup_proxies(self):
        self.name.grab_focus()
        self.add_proxy(self.model, ['name', 'color'])

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
