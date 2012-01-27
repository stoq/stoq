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

import gtk
from kiwi.utils import gsignal
from kiwi.decorators import signal_block
from kiwi.datatypes import ValidationError
from kiwi.ui.delegates import GladeSlaveDelegate

from stoqlib.api import api
from stoqlib.domain.sale import SaleView, Sale
from stoqlib.domain.till import Till
from stoqlib.domain.inventory import Inventory
from stoqlib.exceptions import StoqlibError, TillError
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.wizards.salequotewizard import SaleQuoteWizard
from stoqlib.gui.printing import print_report
from stoqlib.lib.invoice import validate_invoice_number
from stoqlib.lib.message import yesno, info, warning
from stoqlib.lib.formatters import get_price_format_str
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

    def __init__(self, conn, model, model_type, visual_mode=False):
        self._proxy = None
        self.model_type = model_type
        self.max_discount = sysparam(conn).MAX_SALE_DISCOUNT
        BaseEditorSlave.__init__(self, conn, model, visual_mode=visual_mode)

    def setup_widgets(self):
        format_str = get_price_format_str()
        self.discount_perc.set_data_format(format_str)
        self.update_widget_status()

    def update_widget_status(self):
        discount_by_value = not self.discount_perc_ck.get_active()
        self.discount_value.set_sensitive(discount_by_value)
        self.discount_perc.set_sensitive(not discount_by_value)

    def update_sale_discount(self):
        if self._proxy is None:
            return
        if self.discount_perc_ck.get_active():
            self._proxy.update('discount_value')
        else:
            self._proxy.update('discount_percentage')

        self.emit('discount-changed')

    def _validate_percentage(self, value, type_text):
        if value >= 100:
            self.model.discount_percentage = 0
            return ValidationError(_(u'%s can not be greater or equal '
                                      'to 100%%.') % type_text)
        if value > self.max_discount:
            self.model.discount_percentage = 0
            return ValidationError(_("%s can not be greater then %d%%")
                                     % (type_text, self.max_discount))
        if value < 0:
            self.model.discount_percentage = 0
            return ValidationError(_("%s can not be less then 0")
                                    % type_text)
        self.update_sale_discount()

    def set_max_discount(self, discount):
        """Set the maximum percentage value for a discount.
        @param discount: the value for a discount.
        @type discount: L{int} in absolute value like 3
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
        return self._validate_percentage(value, _('Discount'))

    def on_discount_value__validate(self, entry, value):
        percentage = value * 100 / self.model.get_total_sale_amount()
        return self._validate_percentage(percentage, _(u'Discount'))

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
    gladefile = "SaleListToolbar"
    gsignal('sale-returned', object)
    gsignal('sale-edited', object)

    def __init__(self, conn, sales, parent=None):
        self.conn = conn
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
        trans = api.new_transaction()
        sale = trans.get(sale_view.sale)
        model = run_dialog(SaleQuoteWizard, self.parent, trans, sale)
        retval = api.finish_transaction(trans, model)
        trans.close()

        if retval:
            self.emit('sale-edited', retval)

    def show_details(self, sale_view=None):
        if sale_view is None:
            sale_view = self.sales.get_selected()
        run_dialog(SaleDetailsDialog, self.parent,
                   self.conn, sale_view)

    def print_sale(self):
        print_report(SalesReport, self.sales, list(self.sales),
                     filters=self._report_filters)

    def return_sale(self):
        assert not Inventory.has_open(self.conn,
                            api.get_current_branch(self.conn))
        try:
            till = Till.get_current(self.conn)
        except TillError, e:
            warning(str(e))
            return

        if till is None:
            return info(_(u'You must open the till first.'))
        sale = self.sales.get_selected()
        retval = return_sale(self.get_parent(), sale, self.conn)
        api.finish_transaction(self.conn, retval)

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
        self._edit_sale(sale)

    def on_details_button__clicked(self, button):
        self.show_details()

    def on_print_button__clicked(self, button):
        self.print_sale()


class SaleReturnSlave(BaseEditorSlave):
    """A slave for sale return data """
    gladefile = 'SaleReturnSlave'
    model_type = Sale
    sale_widgets = ('order_total',
                    'cancel_date')
    renegotiationdata_widgets = ('responsible',
                                 'reason',
                                 'invoice_number',
                                 'return_total',
                                 'paid_total',
                                 'penalty_value')
    salereturn_widgets = ('cancellation_type',
                          'return_value_desc')
    proxy_widgets = (renegotiationdata_widgets + salereturn_widgets +
                     sale_widgets)
    gsignal('on-penalty-changed', object)

    def __init__(self, conn, model, return_data, visual_mode=False):
        self._return_data = return_data
        # Visual mode only shows details of returned sale, without need a till.
        if not visual_mode:
            self._till = Till.get_current(conn)
        BaseEditorSlave.__init__(self, conn, model, visual_mode=visual_mode)

    def _hide_status_widgets(self):
        for widget in [self.status_label, self.cancellation_type,
                       self.cancellation_details_button,
                       self.return_value_desc, self.cancel_date_label,
                       self.cancel_date]:
            widget.hide()

    def _setup_widgets(self):
        if not self.visual_mode:
            has_paid_value = self._return_data.paid_total > 0
            self.penalty_value.set_sensitive(has_paid_value)
            self._hide_status_widgets()

        if self._return_data.new_order is None:
            self.new_order_button.hide()
        else:
            self.new_order_button.show()

        # TODO to be implemented on bugs 2230 and 2190
        self.cancellation_details_button.hide()

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self._setup_widgets()

        widgets = SaleReturnSlave.renegotiationdata_widgets
        self.adaptable_proxy = self.add_proxy(self._return_data, widgets)

        self.sale_proxy = self.add_proxy(self.model,
                                         SaleReturnSlave.sale_widgets)

        widgets = SaleReturnSlave.salereturn_widgets
        self.return_proxy = self.add_proxy(self._return_data, widgets)

        invoice_number = Sale.get_last_invoice_number(self.conn)
        self.invoice_number.update(invoice_number + 1)

    #
    # Kiwi callbacks
    #

    def on_penalty_value__validate(self, entry, value):
        if self.visual_mode:
            return
        if value < 0:
            return ValidationError(_(u"Deduction value can not be "
                                      "lesser then 0"))
        if value > self._return_data.paid_total:
            return ValidationError(_(u"Deduction value can not be greater "
                                      "then the paid value"))
        till_balance = self._till.get_balance()
        if self._return_data.paid_total > till_balance:
            return ValidationError(_(u'You do not have this value on till.'))

    def after_penalty_value__changed(self, *args):
        model = self.adaptable_proxy.model
        self.emit('on-penalty-changed', model.get_return_total())
        self.adaptable_proxy.update('return_total')

    def on_cancellation_details_button__clicked(self, *args):
        # TODO to be implemented on bugs 2230 and 2190
        pass

    def on_new_order_button__clicked(self, button):
        new_order = self._return_data.new_order
        if not new_order:
            raise StoqlibError("The renegotiation instance must have a "
                               "new_order attribute set at this point")
        sale_view = SaleView.select(SaleView.q.id == new_order.id,
                                    connection=self.conn)[0]
        run_dialog(SaleDetailsDialog, self, self.conn, sale_view)

    def on_invoice_number__validate(self, widget, value):
        return validate_invoice_number(value, self.conn)

# helper functions


def cancel_sale(sale):
    msg = _('Do you really want to cancel this sale ?')
    if yesno(msg, gtk.RESPONSE_NO, _("Cancel sale"), _("Don't cancel sale")):
        sale.cancel()
        return True
    return False


def return_sale(parent, sale_view, conn):
    from stoqlib.gui.wizards.salereturnwizard import SaleReturnWizard
    sale = Sale.get(sale_view.id, connection=conn)
    if sale.can_return():
        retval = run_dialog(SaleReturnWizard, parent, conn, sale_view)
    elif sale.can_cancel():
        retval = cancel_sale(sale)
    else:
        retval = False

    return retval
