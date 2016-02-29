# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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

"""Wizard for work order pre-sales"""

import decimal
import pango

import gtk
from kiwi.currency import currency
from kiwi.ui.objectlist import Column
from kiwi.ui.widgets.combo import ProxyComboBox

from stoqlib.api import api
from stoqlib.domain.sale import Sale
from stoqlib.domain.workorder import (WorkOrder, WorkOrderCategory,
                                      WorkOrderItem)
from stoqlib.gui.base.wizards import BaseWizardStep
from stoqlib.gui.slaves.workorderslave import WorkOrderQuoteSlave
from stoqlib.gui.widgets.notebookbutton import NotebookCloseButton
from stoqlib.gui.wizards.salequotewizard import (SaleQuoteWizard,
                                                 StartSaleQuoteStep,
                                                 SaleQuoteItemStep)
from stoqlib.lib.formatters import (format_sellable_description,
                                    format_quantity, get_formatted_percentage)
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext as _

# The of radio buttons that will fit confortably in the wizard. If the sale
# has more than this number of work orders, then it will be displayed as a
# combo box instead of radio buttons
_MAX_WORK_ORDERS_FOR_RADIO = 3


class _WorkOrderQuoteSlave(WorkOrderQuoteSlave):
    # The description entry is needed here to describe each O.S.
    show_description_entry = True


class WorkOrderQuoteStartStep(StartSaleQuoteStep):
    """First step for work order pre-sales

    Just like
    :class:`stoqlib.gui.wizards.salequotewizard.StartSaleQuoteStep`,
    but the work order category can be selected on it and the next
    step is :class:`.WorkOrderStep`
    """

    gladefile = 'WorkOrderQuoteStartStep'
    model_type = Sale

    #
    #  StartSaleQuoteStep
    #

    def post_init(self):
        self.client.mandatory = True
        super(WorkOrderQuoteStartStep, self).post_init()

    def next_step(self):
        #self.wizard.wo_category = self.wo_categories.get_selected()
        self.wizard.workorders = []
        return WorkOrderQuoteWorkOrderStep(
            self.store, self.wizard, self, self.model)

    def setup_proxies(self):
        self._fill_wo_categories_combo()
        super(WorkOrderQuoteStartStep, self).setup_proxies()

    #
    #  Private
    #

    def _fill_wo_categories_combo(self):
        wo_categories = list(self.store.find(WorkOrderCategory))
        self.wo_categories.color_attribute = 'color'

        self.wo_categories.prefill(
            api.for_combo(wo_categories, empty=_("No category")))
        self.wo_categories.set_sensitive(len(wo_categories))

        # We can use any work order, since all workorders in the same sale are
        # sharing the same category.
        workorder = WorkOrder.find_by_sale(self.store, self.model).any()
        if workorder and workorder.category:
            self.wo_categories.select(workorder.category)

    #
    #  Callbacks
    #

    def on_wo_categories__content_changed(self, combo):
        self.wizard.wo_category = combo.get_selected()


class WorkOrderQuoteWorkOrderStep(BaseWizardStep):
    """Second step for work order pre-sales

    In this step, the sales person can/will create the workorder(s)
    required for this sale (one for each spectacles)
    """

    gladefile = 'WorkOrderQuoteWorkOrderStep'

    def __init__(self, store, wizard, previous, model):
        self.model = model
        BaseWizardStep.__init__(self, store, wizard, previous)
        self._work_order_ids = {0}
        self._create_ui()

    #
    #  Public API
    #

    def get_work_order_slave(self, work_order):
        """Get a slave for the |workorder|

        This is the slave that will be added for each created work order.
        Subclasses can override this to change it.
        """
        # WorkOrderQuoteSlave needs this
        self.edit_mode = self.wizard.edit_mode
        return _WorkOrderQuoteSlave(self.store, work_order)

    #
    #  BaseWizardStep
    #

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def next_step(self):
        return WorkOrderQuoteItemStep(
            self.wizard, self, self.store, self.model)

    #
    #  Private
    #

    def _create_ui(self):
        new_button = gtk.Button(gtk.STOCK_NEW)
        new_button.set_use_stock(True)
        new_button.set_relief(gtk.RELIEF_NONE)
        new_button.show()
        new_button.connect('clicked', self._on_new_work_order__clicked)
        self.work_orders_nb.set_action_widget(new_button, gtk.PACK_END)
        self.new_tab_button = new_button

        saved_orders = list(WorkOrder.find_by_sale(self.store, self.model))
        # This sale does not have any work order yet. Create the first for it
        if not saved_orders:
            self._add_work_order(self._create_work_order())
            return

        # This sale already have some orders, restore them so the user can edit
        for order in saved_orders:
            self._add_work_order(order)

    def _create_work_order(self):
        return WorkOrder(
            store=self.store,
            sale=self.model,
            sellable=None,
            description=u'',
            branch=api.get_current_branch(self.store),
            client=self.model.client)

    def _add_work_order(self, work_order):
        self.wizard.workorders.append(work_order)

        work_order_id = max(self._work_order_ids) + 1
        self._work_order_ids.add(work_order_id)
        # TRANSLATORS: WO is short for Work Order
        label = _('WO %d') % (work_order_id)

        button = NotebookCloseButton()
        hbox = gtk.HBox(spacing=6)
        hbox.pack_start(gtk.Label(label))
        hbox.pack_start(button)
        hbox.show_all()

        holder = gtk.EventBox()
        holder.show()
        slave = self.get_work_order_slave(work_order)
        slave.close_button = button
        self.work_orders_nb.append_page(holder, hbox)
        self.attach_slave(label, slave, holder)
        button.connect('clicked', self._on_remove_work_order__clicked, holder,
                       label, work_order, work_order_id)

    def _remove_work_order(self, holder, name, work_order, work_order_id):
        if work_order.is_finished():
            warning(_("You cannot remove workorder with the status '%s'")
                    % work_order.status_str)
            return
        if not work_order.get_items().find().is_empty():
            warning(_("This workorder already has items and cannot be removed"))
            return

        # We cannot remove the WO from the database (since it already has some
        # history), but we can disassociate it from the sale, cancel and leave
        # a reason for it.
        reason = (_(u'Removed from sale %s') % work_order.sale.identifier)
        work_order.sale = None
        work_order.cancel(reason=reason)

        self._work_order_ids.remove(work_order_id)

        # Remove the tab
        self.detach_slave(name)
        pagenum = self.work_orders_nb.page_num(holder)
        self.work_orders_nb.remove_page(pagenum)

        # And remove the WO
        self.wizard.workorders.remove(work_order)

        self.force_validation()

    #
    #   Kiwi callbacks
    #

    def _on_new_work_order__clicked(self, button):
        self._add_work_order(self._create_work_order())

    def _on_remove_work_order__clicked(self, button, slave_holder, slave_name,
                                       work_order, work_order_id):
        # FIXME: Hide the button from the
        # Dont let the user remove the last WO
        total_pages = self.work_orders_nb.get_n_pages()
        if total_pages == 1:
            return

        self._remove_work_order(slave_holder, slave_name,
                                work_order, work_order_id)


class WorkOrderQuoteItemStep(SaleQuoteItemStep):
    """Third step for work order pre-sales

    Just like :class:`stoqlib.gui.wizards.salequotewizard.SaleQuoteItemStep`,
    but each item added here will be added to a workorder too (selected
    on a combo).
    """

    #
    #  Public API
    #

    def get_extra_columns(self):
        """Get some extra columns for the items list

        Subclasses can override this and add some extra columns. Those
        columns will be added just after the 'description' and before
        the 'quantity' columns.
        """
        return [Column('_equipment', title=_(u'Equipment'), data_type=str,
                       ellipsize=pango.ELLIPSIZE_END)]

    def setup_work_order(self, work_order):
        """Do some extra setup for the work order

        This is called at the initialization of this step. Subclasses can
        override this to do any extra setup they need on the work order.

        :param work_order: the |workorder| we are describing
        """

    #
    #  SaleQuoteItemStep
    #

    def setup_proxies(self):
        self._radio_group = None
        self._setup_work_orders_widgets()
        super(WorkOrderQuoteItemStep, self).setup_proxies()

    def get_order_item(self, sellable, price, quantity, batch=None, parent=None):
        item = super(WorkOrderQuoteItemStep, self).get_order_item(
            sellable, price, quantity, batch=batch, parent=parent)

        work_order = self._selected_workorder
        wo_item = work_order.add_sellable(
            sellable, price=price, batch=batch, quantity=quantity)
        wo_item.sale_item = item
        item._equipment = work_order.description

        return item

    def get_saved_items(self):
        for item in super(WorkOrderQuoteItemStep, self).get_saved_items():
            wo_item = WorkOrderItem.get_from_sale_item(self.store, item)
            item._equipment = wo_item.order.description
            yield item

    def remove_items(self, items):
        # Remove the workorder items first to avoid reference problems
        for item in items:
            wo_item = WorkOrderItem.get_from_sale_item(self.store, item)
            wo_item.order.remove_item(wo_item)

        super(WorkOrderQuoteItemStep, self).remove_items(items)

    def get_columns(self):
        columns = [
            Column('sellable.code', title=_(u'Code'),
                   data_type=str, visible=False),
            Column('sellable.barcode', title=_(u'Barcode'),
                   data_type=str, visible=False),
            Column('sellable.description', title=_('Description'),
                   data_type=str, expand=True,
                   format_func=self._format_description, format_func_data=True),
        ]
        columns.extend(self.get_extra_columns())
        columns.extend([
            Column('quantity', title=_(u'Quantity'),
                   data_type=decimal.Decimal, format_func=format_quantity),
            Column('base_price', title=_('Original Price'), data_type=currency),
            Column('price', title=_('Sale Price'), data_type=currency),
            Column('sale_discount', title=_('Discount'),
                   data_type=decimal.Decimal,
                   format_func=get_formatted_percentage),
            Column('total', title=_(u'Total'),
                   data_type=currency),
        ])
        return columns

    def validate_step(self):
        # When finishing the wizard, make sure that all modifications on
        # sale items on this step are propagated to their work order items
        for sale_item in self.model.get_items():
            wo_item = WorkOrderItem.get_from_sale_item(self.store, sale_item)
            wo_item.quantity = sale_item.quantity
            wo_item.quantity_decreased = sale_item.quantity_decreased
            wo_item.price = sale_item.price

        return super(WorkOrderQuoteItemStep, self).validate_step()

    #
    #  Private
    #

    def _format_description(self, item, data):
        return format_sellable_description(item.sellable, item.batch)

    def _setup_work_orders_widgets(self):
        self._work_orders_hbox = gtk.HBox(spacing=6)
        self.item_vbox.pack_start(self._work_orders_hbox, False, True, 6)
        self.item_vbox.reorder_child(self._work_orders_hbox, 0)
        self._work_orders_hbox.show()

        label = gtk.Label(_("Work order:"))
        self._work_orders_hbox.pack_start(label, False, True)

        data = []
        for wo in self.wizard.workorders:
            # The work order might be already approved if we are editing a sale
            if wo.can_approve():
                wo.approve()

            self.setup_work_order(wo)
            data.append([wo.description, wo])

        if len(data) <= _MAX_WORK_ORDERS_FOR_RADIO:
            self.work_orders_combo = None
            for desc, wo in data:
                self._add_work_order_radio(desc, wo)
        else:
            self.work_orders_combo = ProxyComboBox()
            self.work_orders_combo.prefill(data)
            self._selected_workorder = self.work_orders_combo.get_selected()
            self._work_orders_hbox.pack_start(self.work_orders_combo,
                                              False, False)

        self._work_orders_hbox.show_all()

    def _add_work_order_radio(self, desc, workorder):
        radio = gtk.RadioButton(group=self._radio_group, label=desc)
        radio.set_data('workorder', workorder)
        radio.connect('toggled', self._on_work_order_radio__toggled)

        if self._radio_group is None:
            self._radio_group = radio
            self._selected_workorder = workorder

        self._work_orders_hbox.pack_start(radio, False, False, 6)
        radio.show_all()

    #
    #  Callbacks
    #

    def on_work_orders_combo__content_changed(self, combo):
        self._selected_workorder = combo.get_selected()

    def _on_work_order_radio__toggled(self, radio):
        if not radio.get_active():
            return
        self._selected_workorder = radio.get_data('workorder')


class WorkOrderQuoteWizard(SaleQuoteWizard):
    """Wizard for work order pre-sales

    This is similar to the regular pre-sale, but has an additional step to
    create some workorders, and the item step is changed a little bit, to allow
    the sales person to select in what work order the item should be added to.
    """

    def __init__(self, store, model=None):
        # Mimic BaseEditorSlave api
        self.edit_mode = model is not None
        self.wo_category = None
        self.workorders = []
        SaleQuoteWizard.__init__(self, store, model=model)

    def get_title(self, model=None):
        return _("Sale with work order")

    def get_first_step(self, store, model):
        return WorkOrderQuoteStartStep(store, self, model)

    def finish(self):
        for wo in self.workorders:
            wo.client = self.model.client
            wo.category = self.wo_category

        super(WorkOrderQuoteWizard, self).finish()
