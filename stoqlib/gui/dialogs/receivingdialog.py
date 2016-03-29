# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
""" Classes for Receiving Order Details Dialog """


import gtk
from kiwi.currency import currency
from kiwi.ui.objectlist import Column, SummaryLabel

from stoqlib.api import api
from stoqlib.domain.receiving import ReceivingOrder
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.formatters import get_formatted_cost
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.labeldialog import SkipLabelsEditor
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.slaves.receivingslave import ReceivingInvoiceSlave
from stoqlib.gui.utils.printing import print_labels

_ = stoqlib_gettext


class ReceivingOrderDetailsDialog(BaseEditor):
    """This dialog shows some important details about purchase receiving
    orders like:

    * history of received products
    * Invoice Details
    * Order details such transporter, supplier, etc.
    """

    title = _("Receiving Order Details")
    hide_footer = True
    size = (850, 400)
    model_type = ReceivingOrder
    gladefile = "ReceivingOrderDetailsDialog"

    def __init__(self, store, model):
        BaseEditor.__init__(self, store, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self.product_list.set_columns(self._get_product_columns())
        products = self.model.get_items(with_children=False)
        # XXX Just a precaution
        self.product_list.clear()
        for product in products:
            self.product_list.append(None, product)
            for child in product.children_items:
                self.product_list.append(product, child)

        value_format = '<b>%s</b>'
        total_label = value_format % api.escape(_("Total:"))
        products_summary_label = SummaryLabel(klist=self.product_list,
                                              column='total',
                                              label=total_label,
                                              value_format=value_format)

        products_summary_label.show()
        self.products_vbox.pack_start(products_summary_label, False)

        label = self.print_labels.get_children()[0]
        label = label.get_children()[0].get_children()[1]
        label.set_label(_(u'Print labels'))

    def _get_product_columns(self):
        return [Column("sellable.code", title=_("Code"), data_type=str,
                       justify=gtk.JUSTIFY_RIGHT, width=130),
                Column("sellable.description", title=_("Description"),
                       data_type=str, width=80, expand=True),
                Column("quantity_unit_string", title=_("Quantity"),
                       data_type=str, width=90,
                       justify=gtk.JUSTIFY_RIGHT),
                Column("cost", title=_("Cost"), width=80,
                       format_func=get_formatted_cost, data_type=currency,
                       justify=gtk.JUSTIFY_RIGHT),
                Column("total", title=_("Total"), justify=gtk.JUSTIFY_RIGHT,
                       data_type=currency, width=100)]

    #
    # BaseEditor Hooks
    #

    def setup_proxies(self):
        receiving_date = self.model.receival_date_str
        branch_name = self.model.branch_name
        text = _('Received in <b>%s</b> for branch <b>%s</b>')
        header_text = text % (api.escape(receiving_date),
                              api.escape(branch_name))
        self.header_label.set_markup(header_text)
        self.add_proxy(self.model, ['notes'])

    def setup_slaves(self):
        self.invoice_slave = ReceivingInvoiceSlave(self.store, self.model,
                                                   visual_mode=True)
        self.attach_slave("details_holder", self.invoice_slave)

    def on_print_labels__clicked(self, button):
        label_data = run_dialog(SkipLabelsEditor, self, self.store)
        if label_data:
            print_labels(label_data, self.store, receiving=self.model)
