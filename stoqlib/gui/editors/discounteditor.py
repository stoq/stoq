# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import collections
import decimal

import gtk
from kiwi.datatypes import ValidationError
from kiwi.python import Settable
from kiwi.ui.forms import TextField

from stoqlib.api import api
from stoqlib.domain.sale import Sale
from stoqlib.domain.event import Event
from stoqlib.domain.loan import Loan
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.credentialsdialog import CredentialsDialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.translation import stoqlib_gettext as _


class DiscountEditor(BaseEditor):
    """An editor for applying discounts

    It has a simple entry that understands discount values and discount
    percentages, for instance, '10.5' to give a $10.5 discount on the
    sale, and '10.5%' to give 10.5% discount on the sale
    """

    title = _('Select discount to apply')
    model_type = object
    confirm_widgets = ['discount']

    @cached_property()
    def fields(self):
        return collections.OrderedDict(
            discount=TextField(_('Discount to apply'), mandatory=True)
        )

    def __init__(self, store, model, user=None, visual_mode=False):
        if not isinstance(model, (Sale, Loan)):
            raise TypeError("Expected Sale or Loan, found: %r" % self.model_type)
        self._user = user
        BaseEditor.__init__(self, store, model=model, visual_mode=visual_mode)

    #
    #  BaseEditor
    #

    def setup_proxies(self):
        self.discount.set_tooltip_text(_("Use absolute or percentage (%) value"))

        # We need to put discount on a proxy or else it won't be validated
        # on it's validate callback
        self.add_proxy(Settable(discount=u''), ['discount'])

    def on_confirm(self):
        price = self.model.get_sale_base_subtotal()
        discount = self._get_discount_percentage()
        new_price = price - (price * discount / 100)

        # If user that authorized the discount is not the current user
        if discount > 0 and self._user is not api.get_current_user(self.store):
            Event.log_sale_discount(store=self.store,
                                    sale_number=self.model.identifier,
                                    user_name=self._user.username,
                                    discount_value=discount,
                                    original_price=price,
                                    new_price=new_price)

        self.model.set_items_discount(self._get_discount_percentage())

    #
    #  Private
    #

    def _get_discount_percentage(self):
        discount = self.discount.get_text().strip()
        discount = discount.replace(',', '.')
        if discount.endswith('%'):
            percentage = True
            discount = discount[:-1]
        else:
            percentage = False

        if not discount:
            return None

        # Don't allow operators or anything else. The rest of the string
        # will be validated by decimal bellow
        if not discount[0].isdigit():
            return None

        try:
            discount = decimal.Decimal(discount)
        except decimal.InvalidOperation:
            return None

        if not percentage:
            discount = (discount / self.model.get_sale_base_subtotal()) * 100

        return discount

    #
    #  Callbacks
    #

    def on_discount__icon_press(self, entry, icon_pos, event):
        if icon_pos != gtk.ENTRY_ICON_SECONDARY:
            return

        # Ask for the credentials of a different user that can possibly allow
        # a bigger discount
        self._user = run_dialog(CredentialsDialog, self, self.store)
        if self._user:
            self.discount.validate(force=True)

    def on_discount__validate(self, widget, value):
        if not value:
            return

        discount = self._get_discount_percentage()
        if discount is None:
            return ValidationError(_("The discount syntax is not valid"))

        self._user = self._user or api.get_current_user(self.store)
        max_discount = self._user.profile.max_discount
        if discount > max_discount:
            return ValidationError(
                _("You are only allowed to give a discount of %d%%") % (
                    max_discount, ))
