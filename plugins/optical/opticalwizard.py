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
""" Wizard for optical pre-sale"""

from decimal import Decimal
import operator

import gtk
from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.ui.forms import PriceField, NumericField
from kiwi.ui.objectlist import Column
from kiwi.utils import gsignal

from stoqlib.api import api
from stoqlib.domain.person import Client, ClientView, SalesPerson
from stoqlib.domain.sale import Sale
from stoqlib.domain.workorder import (WorkOrder, WorkOrderCategory,
                                      WorkOrderItem)
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.wizards import BaseWizardStep, WizardEditorStep
from stoqlib.gui.dialogs.batchselectiondialog import BatchDecreaseSelectionDialog
from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.editors.personeditor import ClientEditor
from stoqlib.gui.utils.printing import print_report
from stoqlib.gui.widgets.notebookbutton import NotebookCloseButton
from stoqlib.gui.wizards.abstractwizard import SellableItemSlave
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.gui.wizards.salequotewizard import SaleQuoteWizard, DiscountEditor
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.message import warning, yesno
from stoqlib.lib.formatters import (format_quantity,
                                    format_sellable_description,
                                    get_formatted_percentage)
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import locale_sorted, stoqlib_gettext

from .opticaldomain import OpticalWorkOrder
from .opticalslave import WorkOrderOpticalSlave
from .opticalreport import OpticalWorkOrderReceiptReport


_ = stoqlib_gettext

# This is the of radio buttons that will fit confortably in the wizard. If the
# sale has more than this number of work orders, then it will be displayed as a
# combo box instead of radio buttons
MAX_WORK_ORDERS_FOR_RADIO = 3


class OpticalStartSaleQuoteStep(WizardEditorStep):
    """First step of the pre-sale for optical stores.

    This is just like the first step of the regular pre-sale, but it has a
    different next step.
    """

    gladefile = 'OpticalSalesPersonStep'
    model_type = Sale
    proxy_widgets = ('client', 'salesperson', 'expire_date')

    def _setup_widgets(self):
        # Salesperson combo
        salespersons = self.store.find(SalesPerson)
        self.salesperson.prefill(api.for_person_combo(salespersons))
        if sysparam(self.store).ACCEPT_CHANGE_SALESPERSON:
            self.salesperson.grab_focus()
        else:
            self.salesperson.set_sensitive(False)

        self._fill_clients_combo()
        self._fill_wo_categories_combo()

    def _fill_clients_combo(self):
        # FIXME: This should not be using a normal ProxyComboEntry,
        #        we need a specialized widget that does the searching
        #        on demand.

        # This is to keep the clients in cache
        clients_cache = list(Client.get_active_clients(self.store))
        clients_cache  # pylint: disable=W0104

        # We are using ClientView here to show the fancy name as well
        clients = ClientView.get_active_clients(self.store)
        items = [(c.get_description(), c.client) for c in clients]
        items = locale_sorted(items, key=operator.itemgetter(0))
        self.client.prefill(items)

        # TODO: Implement a has_items() in kiwi
        self.client.set_sensitive(len(self.client.get_model()))

    def _fill_wo_categories_combo(self):
        wo_categories = list(self.store.find(WorkOrderCategory))
        self.wo_categories.color_attribute = 'color'

        if len(wo_categories) > 0:
            items = [(category.get_description(), category)
                     for category in wo_categories]
            items = locale_sorted(items, key=operator.itemgetter(0))
            items.insert(0, ('No category', None))
            self.wo_categories.prefill(items)
            self.wo_categories.set_sensitive(True)

        # We can use any work order, since all workorders in the same sale are
        # sharing the same category.
        workorder = WorkOrder.find_by_sale(self.store, self.model).any()
        if workorder and workorder.category:
            self.wo_categories.select(workorder.category)

    def post_init(self):
        self.toogle_client_details()
        self.client.mandatory = True
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def next_step(self):
        self.wizard.wo_category = self.wo_categories.get_selected()
        return OpticalWorkOrderStep(self.store, self.wizard, self, self.model)

    def has_previous_step(self):
        return False

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    OpticalStartSaleQuoteStep.proxy_widgets)

    def toogle_client_details(self):
        client = self.client.read()
        self.client_details.set_sensitive(bool(client))

    #
    #   Callbacks
    #

    def on_create_client__clicked(self, button):
        store = api.new_store()
        client = run_person_role_dialog(ClientEditor, self.wizard, store, None)
        retval = store.confirm(client)
        client = self.store.fetch(client)
        store.close()
        if retval:
            self._fill_clients_combo()
            self.client.select(client)

    def on_client__changed(self, widget):
        self.toogle_client_details()

    def on_client_details__clicked(self, button):
        client = self.model.client
        run_dialog(ClientDetailsDialog, self.wizard, self.store, client)

    def on_expire_date__validate(self, widget, value):
        if value < localtoday().date():
            msg = _(u"The expire date must be set to today or a future date.")
            return ValidationError(msg)

    def on_observations_button__clicked(self, *args):
        run_dialog(NoteEditor, self.wizard, self.store, self.model, 'notes',
                   title=_("Additional Information"))


class OpticalWorkOrderStep(BaseWizardStep):
    """Second step of the pre-sale for optical stores.

    In this step, the sales person will create the workorders required for this
    sale (one for each spectacles)
    """
    gladefile = 'SaleQuoteWorkOrderStep'

    def __init__(self, store, wizard, previous, model):
        self.model = model
        BaseWizardStep.__init__(self, store, wizard, previous)
        self._work_order_ids = {0}
        self._create_ui()

    #
    #   Private API
    #

    def _create_work_order(self):
        wo = WorkOrder(
            store=self.store,
            sale=self.model,
            equipment=u'',
            branch=api.get_current_branch(self.store),
            client=self.model.client)
        return wo

    def _create_ui(self):
        new_button = gtk.Button(gtk.STOCK_NEW)
        new_button.set_use_stock(True)
        new_button.set_relief(gtk.RELIEF_NONE)
        new_button.show()
        new_button.connect('clicked', self._on_new_work_order__clicked)
        self.work_orders_nb.set_action_widget(new_button, gtk.PACK_END)
        self.new_tab_button = new_button

        saved_orders = list(WorkOrder.find_by_sale(self.store, self.model))
        # This sale does not have any work order yet. Create the first for it.
        if not saved_orders:
            self._add_work_order(self._create_work_order())
            return

        # This sale already have some workorders, restore them so the user can
        # edit
        for order in saved_orders:
            self._add_work_order(order)

    def _add_work_order(self, work_order):
        self.wizard.workorders.add(work_order)

        work_order_id = max(self._work_order_ids) + 1
        self._work_order_ids.add(work_order_id)
        # Translators: WO is short for Work Order
        label = _('WO %d') % (work_order_id)

        button = NotebookCloseButton()
        hbox = gtk.HBox(spacing=6)
        hbox.pack_start(gtk.Label(label))
        hbox.pack_start(button)
        hbox.show_all()

        holder = gtk.EventBox()
        holder.show()
        slave = WorkOrderOpticalSlave(self.store, work_order,
                                      show_finish_date=True)
        slave.close_button = button
        self.work_orders_nb.append_page(holder, hbox)
        self.attach_slave(label, slave, holder)
        button.connect('clicked', self._on_remove_work_order__clicked, holder,
                       work_order, work_order_id)

    def _remove_work_order(self, holder, work_order, work_order_id):
        if not work_order.get_items().find().is_empty():
            warning(_('This workorder already has items and cannot be removed'))
            return

        self._work_order_ids.remove(work_order_id)

        # Remove the tab
        pagenum = self.work_orders_nb.page_num(holder)
        self.work_orders_nb.remove_page(pagenum)

        # And remove the WO
        self.wizard.workorders.remove(work_order)

        # We cannot remove the WO from the database (since it already has some
        # history), but we can disassociate it from the sale and cancel it.
        work_order.sale = None
        work_order.cancel()

    #
    #   BaseWizardStep hooks
    #

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def next_step(self):
        return OpticalItemStep(self.wizard, self, self.store, self.model)

    #
    #   Kiwi callbacks
    #

    def _on_new_work_order__clicked(self, button):
        self._add_work_order(self._create_work_order())

    def _on_remove_work_order__clicked(self, button, slave_holder, work_order,
                                       work_order_id):
        # Dont let the user remove the last WO. TODO: Hide the button from the
        # last tab.
        total_pages = self.work_orders_nb.get_n_pages()
        if total_pages == 1:
            return

        self._remove_work_order(slave_holder, work_order, work_order_id)


# This is used so we can display on what work order an item is in.
class _TempSaleItem(object):
    def __init__(self, sale_item):
        self._sale_item = sale_item

        self.sellable = sale_item.sellable
        self.base_price = sale_item.base_price
        self.price = sale_item.price
        self.quantity = sale_item.quantity
        self.total = sale_item.get_total()
        self.batch = sale_item.batch

        store = sale_item.store
        self._work_item = WorkOrderItem.get_from_sale_item(store, sale_item)
        optical_wo = store.find(OpticalWorkOrder,
                                work_order=self._work_item.order).one()
        self.patient = optical_wo.patient

    @property
    def description(self):
        return format_sellable_description(self.sellable, self.batch)

    @property
    def sale_discount(self):
        return self._sale_item.get_sale_discount()

    def set_discount(self, discount):
        self._sale_item.set_discount(discount)
        self.price = self._sale_item.price
        self.update()

    def remove(self):
        # First remove the item from the work order
        work_order = self._work_item.order
        work_order.remove_item(self._work_item)

        # then remove it from the sale
        sale = self._sale_item.sale
        sale.remove_item(self._sale_item)

    def update(self):
        self._work_item.price = self.price
        self._work_item.quantity = self.quantity
        self._sale_item.price = self.price
        self._sale_item.quantity = self.quantity

        self.total = self._sale_item.get_total()


class _ItemEditor(BaseEditor):
    model_name = _(u'Work order item')
    model_type = _TempSaleItem
    confirm_widgets = ['price', 'quantity']

    fields = dict(
        price=PriceField(_(u'Price'), proxy=True, mandatory=True),
        quantity=NumericField(_(u'Quantity'), proxy=True, mandatory=True),
    )

    def on_confirm(self):
        self.model.update()

    def on_price__validate(self, widget, value):
        if value <= 0:
            return ValidationError(_(u"The price must be greater than 0"))

        sellable = self.model.sellable
        if not sellable.is_valid_price(value):
            return ValidationError(_(u"Max discount for this product "
                                     u"is %.2f%%") % sellable.max_discount)

    def on_quantity__validate(self, entry, value):
        sellable = self.model.sellable

        # TODO: Validate quantity properly (checking if the current stock is
        # enougth
        if value <= 0:
            return ValidationError(_(u"The quantity must be greater than 0"))

        if not sellable.is_valid_quantity(value):
            return ValidationError(_(u"This product unit (%s) does not "
                                     u"support fractions.") %
                                   sellable.get_unit_description())


class _ItemSlave(SellableItemSlave):
    """This is the slave that will add the items in the sale and at the same
    time, also add the items to the Work Orders.

    It will emit a the 'get-work-order' signal when the user is adding a new
    item to the sale. The callback should return the |workorder| that the item
    should be added to.
    """
    gsignal('get-work-order', retval=object)

    model_type = Sale
    batch_selection_dialog = BatchDecreaseSelectionDialog
    item_editor = _ItemEditor
    summary_label_text = "<b>%s</b>" % api.escape(_('Total:'))
    value_column = 'price'
    validate_price = True

    #
    #   SellableItemSlave implementation
    #

    def setup_slaves(self):
        SellableItemSlave.setup_slaves(self)

        self.discount_btn = self.slave.add_extra_button(label=_("Apply discount"))
        self.discount_btn.set_sensitive(False)
        self.slave.klist.connect('has-rows', self._on_klist__has_rows)

    def get_order_item(self, sellable, price, quantity, batch=None):
        work_order = self.emit('get-work-order')
        assert work_order

        sale_item = self.model.add_sellable(sellable, quantity, price, batch=batch)

        remaining_quantity = self.get_remaining_quantity(sellable, batch)
        if remaining_quantity is not None:
            available_quantity = min(quantity, remaining_quantity)
        else:
            available_quantity = quantity

        # Decrease the available  quantity, so it does not get decreased twice
        # when confirming the sale
        sale_item.quantity_decreased = available_quantity

        # Add only the avaiable quantity to the work order, so when it calls
        # sync_stock below, the final quantity in the stock will be correct
        order_item = work_order.add_sellable(sellable, price=price, batch=batch,
                                             quantity=available_quantity)
        order_item.sale_item = sale_item
        return _TempSaleItem(sale_item)

    def get_saved_items(self):
        sale_items = self.model.get_items()
        for item in sale_items:
            yield _TempSaleItem(item)

    def remove_items(self, items):
        for temp_item in items:
            temp_item.remove()

    def get_columns(self, editable=True):
        return [
            Column('sellable.code', title=_(u'Code'),
                   data_type=str, visible=False),
            Column('sellable.barcode', title=_(u'Barcode'),
                   data_type=str, visible=False),
            Column('description', title=_(u'Description'),
                   data_type=str, expand=True),
            Column('patient', title=_(u'Owner'), data_type=str),
            Column('quantity', title=_(u'Quantity'),
                   data_type=Decimal, format_func=format_quantity),
            Column('base_price', title=_('Original Price'), data_type=currency),
            Column('price', title=_('Sale Price'), data_type=currency),
            Column('sale_discount', title=_('Discount'), data_type=Decimal,
                   format_func=get_formatted_percentage),
            Column('total', title=_(u'Total'),
                   data_type=currency),
        ]

    #
    #  Private
    #

    def _show_discount_editor(self):
        rv = run_dialog(DiscountEditor, self.parent, self.store,
                        user=self.manager or api.get_current_user(self.store))
        if not rv:
            return

        for item in self.slave.klist:
            item.set_discount(rv.discount)
            self.slave.klist.update(item)

        self.update_total()

    #
    #  Callbacks
    #

    def _on_klist__has_rows(self, klist, has_rows):
        self.discount_btn.set_sensitive(has_rows)

    def on_discount_btn__clicked(self, button):
        self._show_discount_editor()


class OpticalItemStep(BaseWizardStep):
    """Third step of the optical pre-sale.

    Besides using the <stoqlib.gui.wizards.abstractwizard.SellableItemSlave> to
    add items to the sale, this step has a widget on the top to let the user
    choose on what work order he is adding the items.

    If the sale has more than 4 work orders, then the widget will be a combo
    box.  Otherwise, there will be up to 3 radio buttons for the user to choose
    the work order.
    """
    gladefile = 'OpticalItemStep'

    def __init__(self, wizard, previous, store, model):
        self.model = model
        BaseWizardStep.__init__(self, store, wizard, previous)
        self._radio_group = None
        self._create_ui()

    def _create_ui(self):
        self._setup_workorders_widget()
        self.item_slave = _ItemSlave(self.store, self.wizard, self.model)
        self.attach_slave('slave_holder', self.item_slave)

        self.item_slave.hide_add_button()
        self.item_slave.cost_label.set_label('Price:')
        self.item_slave.cost.set_editable(True)

    def _add_radio(self, desc, workorder):
        widget = gtk.RadioButton(self._radio_group, desc)
        widget.set_data('workorder', workorder)
        widget.connect('toggled', self._on_radio__toggled)
        if self._radio_group is None:
            self._radio_group = widget
            self._selected_workorder = workorder
        self.work_orders_box.pack_start(widget, False, False, 6)
        widget.show()

    def _setup_workorders_widget(self):
        data = []
        for wo in self.wizard.workorders:
            optical_wo = self.store.find(OpticalWorkOrder, work_order=wo).one()
            desc = _('Work order for %s') % optical_wo.patient
            wo.equipment = desc
            wo.estimated_start = wo.estimated_finish

            # The work order might be already approved, if we are editing a
            # sale.
            if wo.can_approve():
                wo.approve()
            data.append([desc, wo])

        if len(data) <= MAX_WORK_ORDERS_FOR_RADIO:
            self.work_orders_combo.hide()
            for desc, wo in data:
                self._add_radio(desc, wo)
        else:
            self.work_orders_box.hide()
            self.work_orders_combo.prefill(data)

    #
    #   Public API
    #

    def get_work_order(self):
        """Returns what |workorder| the user has selected.
        """
        if self.work_orders_combo.get_visible():
            return self.work_orders_combo.read()
        else:
            return self._selected_workorder

    #
    #   Wizard Step Implementation
    #

    def has_next_step(self):
        return False

    #
    #   Callbacks
    #

    def on_item_slave__get_work_order(self, widget):
        return self.get_work_order()

    def _on_radio__toggled(self, radio):
        if not radio.get_active():
            return
        self._selected_workorder = radio.get_data('workorder')


class OpticalSaleQuoteWizard(SaleQuoteWizard):
    """Wizard for optical pre-sales.

    This is similar to the regular pre-sale, but has an additional step to
    create some workorders, and the item step is changed a little bit, to allow
    the sales person to select in what work order the item should be added to.
    """
    def __init__(self, *args, **kwargs):
        self.workorders = set()
        SaleQuoteWizard.__init__(self, *args, **kwargs)

    def get_first_step(self, store, model):
        return OpticalStartSaleQuoteStep(store, self, model)

    def print_quote_details(self, model, payments_created=False):
        msg = _('Would you like to print the quote details now?')
        # We can only print the details if the quote was confirmed.
        if yesno(msg, gtk.RESPONSE_YES,
                 _("Print quote details"), _("Don't print")):
            orders = WorkOrder.find_by_sale(self.model.store, self.model)
            print_report(OpticalWorkOrderReceiptReport, list(orders))

    def finish(self):
        # Now we must remove the products added to the workorders from the
        # stock and we can associate the category selected to the workorders
        # (we only do this now so we don't have to pay attention if the user
        # changes the category after we have created workorders).
        for wo in self.workorders:
            wo.category = self.wo_category
            wo.sync_stock()

        SaleQuoteWizard.finish(self)
