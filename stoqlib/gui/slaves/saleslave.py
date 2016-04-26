#-*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2009 Async Open Source <http://www.async.com.br>
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
""" Slaves for sale management """
from decimal import Decimal

import gtk
from kiwi.datatypes import ValidationError
from kiwi.decorators import signal_block
from kiwi.ui.delegates import GladeSlaveDelegate
from kiwi.utils import gsignal

from stoqlib.api import api
from stoqlib.domain.events import SaleAvoidCancelEvent
from stoqlib.domain.inventory import Inventory
from stoqlib.domain.sale import Sale
from stoqlib.domain.workorder import WorkOrder
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.credentialsdialog import CredentialsDialog
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.utils.printing import print_report
from stoqlib.gui.wizards.salequotewizard import SaleQuoteWizard
from stoqlib.gui.wizards.workorderquotewizard import WorkOrderQuoteWizard
from stoqlib.lib.defaults import quantize
from stoqlib.lib.formatters import get_price_format_str
from stoqlib.lib.message import yesno, warning
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.sale import SalesReport

_ = stoqlib_gettext


class SaleDiscountSlave(BaseEditorSlave):
    """A slave for discounts management
    """
    gladefile = 'SaleDiscountSlave'
    proxy_widgets = ('discount_value',
                     'discount_perc', )
    gsignal('discount-changed')

    def __init__(self, store, model, model_type, visual_mode=False):
        self._proxy = None
        self.model = model
        self.model_type = model_type
        self.manager = None
        self.default_max_discount = sysparam.get_decimal('MAX_SALE_DISCOUNT')
        self.max_discount = self.default_max_discount
        # If there is an original discount, this means the sale was from a trade,
        # and the parameter USE_TRADE_AS_DISCOUNT must be set.
        self.original_discount = self.model.discount_value * 100 / self.model.get_sale_subtotal()
        if self.original_discount:
            assert sysparam.get_bool('USE_TRADE_AS_DISCOUNT')
        self.original_sale_amount = self.model.get_total_sale_amount()
        BaseEditorSlave.__init__(self, store, model, visual_mode=visual_mode)

    def setup_widgets(self):
        format_str = get_price_format_str()
        self.discount_perc.set_data_format(format_str)
        self.update_widget_status()

    def update_widget_status(self):
        discount_by_value = not self.discount_perc_ck.get_active()
        self.discount_value.set_sensitive(discount_by_value)
        self.discount_perc.set_sensitive(not discount_by_value)

    def update_max_discount(self):
        old_max_discount = self.max_discount
        self.max_discount = self.default_max_discount

        client = self.model.client
        if client and client.category:
            self.max_discount = max(client.category.max_discount,
                                    self.default_max_discount)
        if self.manager:
            self.max_discount = max(self.max_discount,
                                    self.manager.profile.max_discount)

        # Avoid re-validating if the validation parameters didnt change, since
        # that is doint to many queries right now.
        if old_max_discount != self.max_discount:
            self.discount_value.validate()
            self.discount_perc.validate()
            self.update_sale_discount()

    def update_sale_discount(self):
        if self._proxy is None:
            return
        if self.discount_perc_ck.get_active():
            self._proxy.update('discount_value')
        else:
            self._proxy.update('discount_percentage')

        self.emit('discount-changed')

    def _run_credentials_dialog(self):
        # Ask for the credentials of a different user that can possibly allow a
        # bigger discount.
        self.manager = run_dialog(CredentialsDialog,
                                  self.get_toplevel().get_toplevel(), self.store)
        self.update_max_discount()

    def _validate_percentage(self, value, type_text):
        if value >= 100:
            self.model.discount_percentage = 0
            return ValidationError(_(u'%s can not be greater or equal '
                                     'to 100%%.') % type_text)
        if value < 0:
            self.model.discount_percentage = 0
            return ValidationError(_("%s can not be less than 0")
                                   % type_text)

        if (not sysparam.get_bool('USE_TRADE_AS_DISCOUNT') and
                value > self.max_discount):
            self.model.discount_percentage = 0
            return ValidationError(_("%s can not be greater than %d%%")
                                   % (type_text, self.max_discount))

        discount = self.max_discount / 100 * self.original_sale_amount
        perc = discount * 100 / self.model.get_sale_subtotal()
        new_discount = quantize(self.original_discount + perc)
        #XXX: If the discount is less than the trade value. What to do?
        if (sysparam.get_bool('USE_TRADE_AS_DISCOUNT') and value > new_discount):
            self.model.discount_percentage = 0
            return ValidationError(_(u'%s can not be greater than (%.2f%%).')
                                   % (type_text, new_discount))

    def set_max_discount(self, discount):
        """Set the maximum percentage value for a discount.
        :param discount: the value for a discount.
        :type discount: :class:`int` in absolute value like 3
        """
        self.max_discount = discount

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self.update_widget_status()
        self._proxy = self.add_proxy(self.model,
                                     SaleDiscountSlave.proxy_widgets)

    #
    # Kiwi callbacks
    #

    def on_discount_perc__validate(self, entry, value):
        if not self.discount_perc.is_sensitive() or self._proxy is None:
            return
        return self._validate_percentage(value, _('Discount'))

    def on_discount_value__validate(self, entry, value):
        if not self.discount_value.is_sensitive() or self._proxy is None:
            return
        percentage = quantize(value * 100 / self.model.get_sale_subtotal())
        # If the quantized percentage value is 100, the value may still be lower
        # then the subtotal. In this case, lets consider the discount percentage
        # to be 99.99 (So that we can close a sale for 0.01, for instance)
        if percentage == 100 and value < self.model.get_sale_subtotal():
            percentage = Decimal('99.99')
        return self._validate_percentage(percentage, _(u'Discount'))

    def on_discount_perc__icon_press(self, entry, icon_pos, event):
        if icon_pos != gtk.ENTRY_ICON_PRIMARY:
            return
        self._run_credentials_dialog()

    def on_discount_value__icon_press(self, entry, icon_pos, event):
        if icon_pos != gtk.ENTRY_ICON_PRIMARY:
            return
        self._run_credentials_dialog()

    @signal_block('discount_value.changed')
    def after_discount_perc__changed(self, *args):
        self.update_sale_discount()

    @signal_block('discount_perc.changed')
    def after_discount_value__changed(self, *args):
        self.update_sale_discount()

    def on_discount_value_ck__toggled(self, *args):
        self.update_widget_status()


class SaleListToolbar(GladeSlaveDelegate):
    """ A simple sale toolbar with common operations like, returning a sale,
    changing installments and showing its details.
    """
    domain = 'stoq'
    gladefile = "SaleListToolbar"
    gsignal('sale-returned', object)
    gsignal('sale-edited', object)

    def __init__(self, store, sales, parent=None):
        self.store = store
        if sales.get_selection_mode() != gtk.SELECTION_BROWSE:
            raise TypeError("Only SELECTION_BROWSE mode for the "
                            "list is supported on this slave")
        self.sales = sales
        self.parent = parent
        self._report_filters = []

        GladeSlaveDelegate.__init__(self)

        self._update_print_button(False)
        self.update_buttons()

    #
    # Public API
    #

    def update_buttons(self):
        sale_view = self.sales.get_selected()
        self.details_button.set_sensitive(bool(sale_view))
        can_return = bool(sale_view and sale_view.can_return())
        can_edit = bool(sale_view and sale_view.status == Sale.STATUS_QUOTE)
        self.return_sale_button.set_sensitive(can_return)
        self.edit_button.set_sensitive(can_edit)

    def set_report_filters(self, filters):
        self._report_filters = filters

    def edit(self, sale_view=None):
        if sale_view is None:
            sale_view = self.sales.get_selected()
        store = api.new_store()
        sale = store.fetch(sale_view.sale)

        # If we have work orders on the sale (the sale is a pre-sale), we need
        # to run WorkOrderQuoteWizard instead of SaleQuoteWizard
        has_workorders = not WorkOrder.find_by_sale(store, sale).is_empty()
        if has_workorders:
            wizard = WorkOrderQuoteWizard
        else:
            wizard = SaleQuoteWizard
        model = run_dialog(wizard, self.parent, store, sale)
        retval = store.confirm(model)
        store.close()

        if retval:
            self.emit('sale-edited', retval)

    def show_details(self, sale_view=None):
        if sale_view is None:
            sale_view = self.sales.get_selected()
        run_dialog(SaleDetailsDialog, self.parent,
                   self.store, sale_view)

    def print_sale(self):
        print_report(SalesReport, self.sales, list(self.sales),
                     filters=self._report_filters)

    def return_sale(self):
        assert not Inventory.has_open(self.store,
                                      api.get_current_branch(self.store))
        sale_view = self.sales.get_selected()
        store = api.new_store()
        retval = return_sale(self.get_parent(),
                             store.fetch(sale_view.sale), store)
        store.confirm(retval)
        store.close()

        if retval:
            self.emit('sale-returned', retval)

    #
    # Private
    #

    def _update_print_button(self, enabled):
        self.print_button.set_sensitive(enabled)

    #
    # Kiwi callbacks
    #

    def on_sales__has_rows(self, klist, enabled):
        self._update_print_button(enabled)

    def on_sales__selection_changed(self, sales, sale):
        self.update_buttons()

    def on_sales__row_activated(self, sales, sale):
        if sale.status == Sale.STATUS_QUOTE:
            self.edit(sale)
        else:
            self.show_details(sale)

    def on_return_sale_button__clicked(self, button):
        self.return_sale()

    def on_edit_button__clicked(self, button):
        sale = self.sales.get_selected()
        self.edit(sale)

    def on_details_button__clicked(self, button):
        self.show_details()

    def on_print_button__clicked(self, button):
        self.print_sale()


def cancel_sale(sale):
    msg = _('Do you really want to cancel this sale ?')
    if yesno(msg, gtk.RESPONSE_NO, _("Cancel sale"), _("Don't cancel sale")):
        sale.cancel()
        return True
    return False


def return_sale(parent, sale, store):
    from stoqlib.gui.wizards.salereturnwizard import SaleReturnWizard

    # A plugin (e.g. ECF) can avoid the cancelation of a sale
    # because it wants it to be cancelled using another way
    if SaleAvoidCancelEvent.emit(sale):
        return

    if sale.can_return():
        need_document = not sysparam.get_bool('ACCEPT_SALE_RETURN_WITHOUT_DOCUMENT')
        if need_document and not sale.get_client_document():
            warning(_('It is not possible to accept a returned sale from clients '
                      'without document. Please edit the client document or change '
                      'the sale client'))
            return

        returned_sale = sale.create_sale_return_adapter()
        retval = run_dialog(SaleReturnWizard, parent, store, returned_sale)
    elif sale.can_cancel():
        retval = cancel_sale(sale)
    else:
        retval = False

    return retval
