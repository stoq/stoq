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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##
""" Slaves for sale management """

import gtk
from kiwi.utils import gsignal
from kiwi.decorators import signal_block
from kiwi.datatypes import ValidationError
from kiwi.ui.delegates import SlaveDelegate
from kiwi.argcheck import argcheck

from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.editors import BaseEditorSlave
from stoqlib.domain.sale import SaleView
from stoqlib.lib.validators import get_price_format_str
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.reporting.sale import SalesReport

_ = stoqlib_gettext


class DiscountChargeSlave(BaseEditorSlave):
    """A slave for discounts and charge management

    Notes:
        after_value_changed_handler     = a function which will be called
                                          always after a discount or charge
                                          is changed
    """
    gladefile = 'DiscountChargeSlave'
    proxy_widgets = ('discount_value',
                     'charge_value',
                     'discount_perc',
                     'charge_perc')
    gsignal('discount-changed')

    def __init__(self, conn, model, model_type):
        self.model_type = model_type
        BaseEditorSlave.__init__(self, conn, model)

    def setup_widgets(self):
        format_str = get_price_format_str()
        for widget in (self.discount_perc, self.charge_perc):
            widget.set_data_format(format_str)
        self.update_widget_status()

    def update_widget_status(self):
        charge_by_value = not self.charge_perc_ck.get_active()
        self.charge_value.set_sensitive(charge_by_value)
        self.charge_perc.set_sensitive(not charge_by_value)

        discount_by_value = not self.discount_perc_ck.get_active()
        self.discount_value.set_sensitive(discount_by_value)
        self.discount_perc.set_sensitive(not discount_by_value)

    def setup_discount_charge(self):
        if self.discount_perc_ck.get_active():
            self.proxy.update('discount_value')
        else:
            self.proxy.update('discount_percentage')

        if self.charge_perc_ck.get_active():
            self.proxy.update('charge_value')
        else:
            self.proxy.update('charge_percentage')
        self.emit('discount-changed')

    def _validate_percentage(self, value, type_text):
        if value > 100:
            return ValidationError(_("%s can not be greater then 100")
                                     % type_text)

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self.setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    DiscountChargeSlave.proxy_widgets)

    #
    # Kiwi callbacks
    #

    def on_charge_perc__validate(self, entry, value):
        return self._validate_percentage(value, _('Charge'))

    def on_discount_perc__validate(self, entry, value):
        return self._validate_percentage(value, _('Discount'))

    @signal_block('discount_value.changed')
    def after_discount_perc__changed(self, *args):
        self.setup_discount_charge()

    @signal_block('discount_perc.changed')
    def after_discount_value__changed(self, *args):
        self.setup_discount_charge()
        if self.model.discount_percentage > 100:
            msg =_("Discount can not be greater then 100 percent")
            self.discount_value.set_invalid(msg)

    @signal_block('charge_value.changed')
    def after_charge_perc__changed(self, *args):
        self.setup_discount_charge()

    @signal_block('charge_perc.changed')
    def after_charge_value__changed(self, *args):
        self.setup_discount_charge()
        if self.model.charge_percentage > 100:
            msg =_("Charge can not be greater then 100 percent")
            self.charge_value.set_invalid(msg)

    def on_charge_perc_ck__toggled(self, *args):
        self.update_widget_status()

    def on_charge_value_ck__toggled(self, *args):
        self.update_widget_status()

    def on_discount_perc_ck__toggled(self, *args):
        self.update_widget_status()

    def on_discount_value_ck__toggled(self, *args):
        self.update_widget_status()


class SaleListToolbar(SlaveDelegate):
    """ A simple sale toolbar with common operations like, returning a sale,
    changing installments and showing its details.
    """
    gladefile = "SaleListToolbar"

    def __init__(self, conn, searchbar, klist, parent=None):
        SlaveDelegate.__init__(self, gladefile=SaleListToolbar.gladefile,
                               toplevel_name=SaleListToolbar.gladefile)
        if klist.get_selection_mode() != gtk.SELECTION_BROWSE:
            raise TypeError("Only SELECTION_BROWSE mode for the "
                            "list is supported on this slave")
        self.conn, self.klist, self.parent = conn, klist, parent
        self.searchbar = searchbar
        self.klist.connect("selection-changed",
                           self.on_klist_selection_changed)
        self.klist.connect("double-click", self.on_klist_double_clicked)
        self.klist.connect("has-rows", self._update_print_button)
        self._update_print_button(None, False)
        self.klist.set_selection_mode(gtk.SELECTION_MULTIPLE)
        self._update_buttons(False)

    def hide_return_sale_button(self):
        self.return_sale_button.hide()

    def hide_edit_button(self):
        self.edit_button.hide()

    def _update_print_button(self, klist, enabled):
        self.print_button.set_sensitive(enabled)

    def _update_buttons(self, enabled):
        for w in (self.return_sale_button,
                  self.edit_button,
                  self.details_button):
            w.set_sensitive(enabled)

    @argcheck(SaleView)
    def _run_details_dialog(self, sale_view):
        run_dialog(SaleDetailsDialog, self.parent, self.conn, sale_view)

    #
    # Kiwi callbacks
    #

    def on_klist_selection_changed(self, widget, sale):
        self._update_buttons(len(sale) == 1)

    def on_klist_double_clicked(self, widget, sale):
        self._run_details_dialog(sale)

    def on_return_sale_button__clicked(self, *args):
        # TODO: implements this method
        pass

    def on_edit_button__clicked(self, *args):
        # TODO: this method will be implemented on bug #2189
        pass

    def on_details_button__clicked(self, *args):
        self._run_details_dialog(self.klist.get_selected_rows()[0])

    def on_print_button__clicked(self, *args):
        self.searchbar.print_report(SalesReport,
                                    (self.klist.get_selected_rows()
                                     or self.klist))
