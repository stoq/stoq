# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2015 Async Open Source <http://www.async.com.br>
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
""" Classes for Transfer Order Details Dialog """

from gi.repository import Gtk
from kiwi.currency import currency
from kiwi.ui.objectlist import Column, SummaryLabel

from stoqlib.api import api
from stoqlib.domain.events import StockOperationTryFiscalCancelEvent
from stoqlib.domain.transfer import TransferOrder, TransferOrderItem
from stoq.lib.gui.base.dialogs import run_dialog
from stoq.lib.gui.editors.baseeditor import BaseEditor
from stoq.lib.gui.editors.noteeditor import NoteEditor
from stoq.lib.gui.utils.printing import print_report
from stoqlib.lib.message import yesno, warning
from stoqlib.lib.pluginmanager import get_plugin_manager
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.transfer import TransferOrderReceipt

_ = stoqlib_gettext


class TransferOrderDetailsDialog(BaseEditor):
    """This dialog shows some important details about transfer orders
    like:

    * The source and destination branches
    * The transfer quantity of each item
    * The cost of each item
    """

    title = _(u"Transfer Order Details")
    hide_footer = True
    size = (700, 400)
    model_type = TransferOrder
    report_class = TransferOrderReceipt
    gladefile = "TransferOrderDetails"
    transfer_widgets = ['open_date',
                        'receival_date',
                        'close_date_lbl',
                        'source_branch_name',
                        'destination_branch_name',
                        'source_responsible_name',
                        'destination_responsible_name',
                        'comments']
    invoice_widgets = ['invoice_number']
    proxy_widgets = transfer_widgets + invoice_widgets

    def __init__(self, store, model):
        BaseEditor.__init__(self, store, model)
        self._setup_widgets()

    def add_tab(self, slave, name):
        """Add a new tab on the notebook

        :param slave: the slave we are attaching to the new tab
        :param name: the name of the tab
        """
        event_box = Gtk.EventBox()
        self.details_notebook.insert_page(event_box, Gtk.Label(label=name), -1)
        self.attach_slave(name, slave, event_box)
        event_box.show()

    def _setup_status(self):
        self.status.set_text(self.model.status_str)

        local_branch = api.get_current_branch(self.store)
        sent_remote_order = (self.model.status == self.model.STATUS_SENT and
                             self.model.destination_branch == local_branch)

        if not sent_remote_order:
            self.receive_button.hide()
        else:
            self.cancel_button.hide()
        if self.model.status == self.model.STATUS_RECEIVED:
            self.close_date_lbl.set_label(_(u"Receival date:"))
            self.cancel_button.hide()
        if self.model.status == self.model.STATUS_CANCELLED:
            self.close_date_lbl.set_label(_(u"Cancel date:"))
            self.cancel_button.hide()

    def _setup_widgets(self):
        self._setup_status()

        self.product_list.set_columns(self._get_product_columns())
        products = self.store.find(TransferOrderItem, transfer_order=self.model)
        self.product_list.add_list(list(products))

        value_format = '<b>%s</b>'
        total_label = value_format % api.escape(_("Total:"))
        products_summary_label = SummaryLabel(klist=self.product_list,
                                              column='total',
                                              label=total_label,
                                              value_format=value_format)
        products_summary_label.show()
        self.products_vbox.pack_start(products_summary_label, False, True, 0)

    def _get_product_columns(self):
        return [Column("sellable.code", title=_("Code"), data_type=str,
                       justify=Gtk.Justification.RIGHT, width=130),
                Column("sellable.description", title=_("Description"),
                       data_type=str, expand=True),
                Column("quantity", title=_("Quantity"),
                       data_type=int, justify=Gtk.Justification.RIGHT),
                Column("sellable.cost", title=_("Cost"), width=100,
                       data_type=currency, justify=Gtk.Justification.RIGHT),
                Column("total", title=_(u"Total Cost"), width=100,
                       data_type=currency, justify=Gtk.Justification.RIGHT)]

    #
    # BaseEditor Hooks
    #

    def setup_proxies(self):
        if self.model.status == TransferOrder.STATUS_CANCELLED:
            self.receival_date.set_property('model-attribute', 'cancel_date')
        elif self.model.status == TransferOrder.STATUS_RECEIVED:
            self.receival_date.set_property('model-attribute', 'receival_date')
        self.transfer_proxy = self.add_proxy(self.model, self.transfer_widgets)
        self.invoice_proxy = self.add_proxy(self.model.invoice, self.invoice_widgets)

    def on_receive_button__clicked(self, event):
        assert self.model.status == self.model.STATUS_SENT

        if yesno(_(u'Receive the order?'), Gtk.ResponseType.YES, _(u'Receive'),
                 _(u"Don't receive")):
            user = api.get_current_user(self.store)
            responsible = user.person.employee
            self.model.receive(user, responsible)
            self.store.commit(close=False)
            self.receival_date.set_property('model-attribute', 'receival_date')
            self.transfer_proxy.update_many(['destination_responsible_name',
                                             'receival_date'])

        self._setup_status()

    def on_cancel_button__clicked(self, event):
        msg_text = _(u'This will cancel the transfer. Are you sure?')

        # nfce plugin cancellation event requires a minimum length for the
        # cancellation reason note. We can't set this in the plugin because it's
        # not possible to identify unically this NoteEditor.
        if get_plugin_manager().is_active('nfce'):
            note_min_length = 15
        else:
            note_min_length = 0

        retval = run_dialog(
            NoteEditor, self, self.model.store, model=None,
            message_text=msg_text, label_text=_(u"Reason"), mandatory=True,
            ok_button_label=_(u"Cancel transfer"),
            cancel_button_label=_(u"Don't cancel"),
            min_length=note_min_length)

        if not retval:
            return

        # Try to cancel the transfer fiscally with a fiscal plugin. If False is
        # returned, the cancellation failed, so we don't proceed.
        if StockOperationTryFiscalCancelEvent.emit(self.model, retval.notes) is False:
            warning(_("The cancellation was not authorized by SEFAZ. You "
                      "should do a reverse transfer."))
            return

        user = api.get_current_user(self.store)
        branch = api.get_current_branch(self.store)
        responsible = user.person.employee
        self.model.cancel(user, responsible, retval.notes, branch)
        self.store.commit(close=False)
        self.receival_date.set_property('model-attribute', 'cancel_date')
        self.transfer_proxy.update_many(['destination_responsible_name',
                                         'receival_date'])
        self.setup_proxies()
        self._setup_status()
    #
    # Callbacks
    #

    def on_print_button__clicked(self, button):
        print_report(self.report_class, self.model)
