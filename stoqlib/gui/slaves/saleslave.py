#-*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
""" Slaves for sale management """

import gtk
from kiwi.utils import gsignal
from kiwi.decorators import signal_block
from kiwi.datatypes import ValidationError
from kiwi.ui.delegates import GladeSlaveDelegate

from stoqlib.database.runtime import finish_transaction
from stoqlib.domain.sale import SaleView, Sale
from stoqlib.exceptions import StoqlibError
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.printing import print_report
from stoqlib.lib.validators import get_price_format_str
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.sale import SalesReport

_ = stoqlib_gettext


class DiscountSurchargeSlave(BaseEditorSlave):
    """A slave for discounts and surcharge management
    """
    gladefile = 'DiscountChargeSlave'
    proxy_widgets = ('discount_value',
                     'surcharge_value',
                     'discount_perc',
                     'surcharge_perc')
    gsignal('discount-changed')

    def __init__(self, conn, model, model_type, visual_mode=False):
        self.model_type = model_type
        self.max_discount = sysparam(conn).MAX_SALE_DISCOUNT
        BaseEditorSlave.__init__(self, conn, model, visual_mode=visual_mode)

    def setup_widgets(self):
        format_str = get_price_format_str()
        for widget in (self.discount_perc, self.surcharge_perc):
            widget.set_data_format(format_str)
        self.update_widget_status()

    def update_widget_status(self):
        surcharge_by_value = not self.surcharge_perc_ck.get_active()
        self.surcharge_value.set_sensitive(surcharge_by_value)
        self.surcharge_perc.set_sensitive(not surcharge_by_value)

        discount_by_value = not self.discount_perc_ck.get_active()
        self.discount_value.set_sensitive(discount_by_value)
        self.discount_perc.set_sensitive(not discount_by_value)

    def setup_discount_surcharge(self):
        if self.discount_perc_ck.get_active():
            self.proxy.update('discount_value')
        else:
            self.proxy.update('discount_percentage')

        if self.surcharge_perc_ck.get_active():
            self.proxy.update('surcharge_value')
        else:
            self.proxy.update('surcharge_percentage')
        self.emit('discount-changed')

    def _validate_percentage(self, value, type_text):
        if value > self.max_discount:
            self.model.discount_percentage = 0
            return ValidationError(_("%s can not be greater then %d%%")
                                     % (type_text, self.max_discount))
        if value < 0:
            self.model.discount_percentage = 0
            return ValidationError(_("%s can not be less then 0")
                                    % type_text)

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self.update_widget_status()
        self.proxy = self.add_proxy(self.model,
                                    DiscountSurchargeSlave.proxy_widgets)

    #
    # Kiwi callbacks
    #

    def on_surcharge_perc__validate(self, entry, value):
        return self._validate_percentage(value, _('Surcharge'))

    def on_discount_perc__validate(self, entry, value):
        return self._validate_percentage(value, _('Discount'))

    @signal_block('discount_value.changed')
    def after_discount_perc__changed(self, *args):
        self.setup_discount_surcharge()

    @signal_block('discount_perc.changed')
    def after_discount_value__changed(self, *args):
        percentage = self.model.discount_percentage
        if percentage > self.max_discount:
            msg = _("Discount can not be greater then %d%%" \
                    % self.max_discount)
            self.discount_value.set_invalid(msg)
            self.model.discount_percentage = 0
        elif self.model.discount_percentage < 0:
            msg = _("Discount can not be negative")
            self.discount_value.set_invalid(msg)
            self.model.discount_percentage = 0

        self.setup_discount_surcharge()

    @signal_block('surcharge_value.changed')
    def after_surcharge_perc__changed(self, *args):
        self.setup_discount_surcharge()

    @signal_block('surcharge_perc.changed')
    def after_surcharge_value__changed(self, *args):
        self.setup_discount_surcharge()

    def on_surcharge_perc_ck__toggled(self, *args):
        self.setup_discount_surcharge()
        self.update_widget_status()

    def on_surcharge_value_ck__toggled(self, *args):
        self.setup_discount_surcharge()
        self.update_widget_status()

    def on_discount_perc_ck__toggled(self, *args):
        self.setup_discount_surcharge()
        self.update_widget_status()

    def on_discount_value_ck__toggled(self, *args):
        self.setup_discount_surcharge()
        self.update_widget_status()


class SaleListToolbar(GladeSlaveDelegate):
    """ A simple sale toolbar with common operations like, returning a sale,
    changing installments and showing its details.
    """
    gladefile = "SaleListToolbar"
    gsignal('sale-returned', object)

    def __init__(self, conn, sales, parent=None):
        self.conn = conn
        if sales.get_selection_mode() != gtk.SELECTION_BROWSE:
            raise TypeError("Only SELECTION_BROWSE mode for the "
                            "list is supported on this slave")
        self.sales = sales
        self.parent = parent

        GladeSlaveDelegate.__init__(self)

        self._update_print_button(False)
        self._update_buttons(False)
        self.edit_button.hide()

    #
    # Public API
    #

    def disable_editing(self):
        """
        Disables editing of the sales
        """
        sale_view = self.sales.get_selected()
        self.details_button.set_sensitive(bool(sale_view))
        can_return = bool(sale_view and sale_view.sale.can_return())
        self.return_sale_button.set_sensitive(can_return)

    #
    # Private
    #

    def _update_buttons(self, enabled):
        if self.disable_editing():
            for w in (self.return_sale_button,
                      self.details_button):
                w.set_sensitive(enabled)

    def _update_print_button(self, enabled):
        self.print_button.set_sensitive(enabled)

    def _show_details(self, sale_view):
        run_dialog(SaleDetailsDialog, self.parent, self.conn, sale_view)

    #
    # Kiwi callbacks
    #

    def on_sales__has_rows(self, klist, enabled):
        self._update_print_button(enabled)

    def on_sales__selection_changed(self, sales, sale):
        self._update_buttons(sale != None)

    def on_sales__row_activated(self, sales, sale):
        self._show_details(sale)

    def on_return_sale_button__clicked(self, button):
        from stoqlib.gui.wizards.salereturnwizard import SaleReturnWizard
        sale = self.sales.get_selected()
        retval = run_dialog(SaleReturnWizard, self.parent, self.conn, sale)
        finish_transaction(self.conn, retval)
        if retval:
            self.emit('sale-returned', retval)

    def on_edit_button__clicked(self, button):
        # TODO: this method will be implemented on bug #2189
        pass

    def on_details_button__clicked(self, button):
        self._show_details(self.sales.get_selected())

    def on_print_button__clicked(self, button):
        print_report(SalesReport, self.sales)

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

    #
    # Kiwi callbacks
    #

    def on_penalty_value__validate(self, entry, value):
        if value < 0 :
            return ValidationError(_(u"Deduction value can not be "
                                      "lesser then 0"))
        if value > self._return_data.paid_total:
            return ValidationError(_(u"Deduction value can not be greater "
                                      "then the paid value"))

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
        sale_view = SaleView.get(new_order.id, connection=self.conn)
        run_dialog(SaleDetailsDialog, self, self.conn, sale_view)
