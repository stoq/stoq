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
##

import datetime

import gtk

from storm.expr import In
from kiwi.ui.gadgets import render_pixbuf
from kiwi.ui.objectlist import Column

from stoqlib.api import api
from stoqlib.domain.inventory import Inventory
from stoqlib.domain.person import Branch
from stoqlib.domain.workorder import (WorkOrder, WorkOrderCategory,
                                      WorkOrderPackage,
                                      WorkOrderApprovedAndFinishedView)
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.editors.noteeditor import NoteEditor, Note
from stoqlib.gui.editors.workordercategoryeditor import WorkOrderCategoryEditor
from stoqlib.gui.search.searchcolumns import IdentifierColumn
from stoqlib.gui.search.sellablesearch import SellableSearch
from stoqlib.gui.slaves.workorderslave import (WorkOrderOpeningSlave,
                                               WorkOrderQuoteSlave,
                                               WorkOrderExecutionSlave,
                                               WorkOrderHistorySlave)
from stoqlib.gui.utils.workorderutils import get_workorder_state_icon
from stoqlib.gui.widgets.queryentry import ClientEntryGadget
from stoqlib.lib.message import warning
from stoqlib.lib.permissions import PermissionManager
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class WorkOrderEditor(BaseEditor):
    """An editor for working with |workorder| objects"""

    size = (800, -1)
    gladefile = 'WorkOrderEditor'
    model_type = WorkOrder
    model_name = _(u'Work order')
    help_section = 'workorder'
    need_cancel_confirmation = True
    proxy_widgets = [
        'category',
        'client',
        'description',
        'identifier',
        'status_str',
        'supplier_order',
        'quantity',
    ]

    def __init__(self, store, model=None, visual_mode=False, category=None,
                 available_categories=None):
        """
        @param category: The default category that should be already selected.
        @param available_categories: A list of categories names that should be
          available to the user. If None, all categoires will be available
        """
        self._default_category = category
        self.categories_for_combo = available_categories
        self.proxy = None
        super(WorkOrderEditor, self).__init__(store, model=model,
                                              visual_mode=visual_mode)
        self._setup_widgets()
        pm = PermissionManager.get_permission_manager()
        if not pm.can_create('WorkOrderCategory'):
            self.category_create.hide()
        if not pm.can_edit('WorkOrderCategory'):
            self.category_edit.hide()

    #
    #  BaseEditor
    #

    def create_model(self, store):
        defect_detected = api.sysparam.get_string('DEFECT_DETECTED_TEMPLATE')
        branch = api.get_current_branch(store)
        return WorkOrder(
            store=store,
            sellable=None,
            description=u'',
            branch=branch,
            category=self._default_category,
            defect_detected=defect_detected,
        )

    def setup_slaves(self):
        self.opening_slave = WorkOrderOpeningSlave(
            self.store, self.model, visual_mode=self.visual_mode,
            edit_mode=self.edit_mode)
        self.attach_slave('opening_holder', self.opening_slave)

        self.quote_slave = WorkOrderQuoteSlave(
            self.store, self.model, visual_mode=self.visual_mode,
            edit_mode=self.edit_mode)
        self.attach_slave('quote_holder', self.quote_slave)

        self.execution_slave = WorkOrderExecutionSlave(
            self, self.store, self.model, visual_mode=self.visual_mode,
            edit_mode=self.edit_mode)
        self.attach_slave('execution_holder', self.execution_slave)

        self.history_slave = WorkOrderHistorySlave(
            self.store, self.model, visual_mode=self.visual_mode,
            edit_mode=self.edit_mode)
        self.attach_slave('history_holder', self.history_slave)

        self._update_view()

    def setup_proxies(self):
        self._fill_categories_combo()
        self._setup_client_widget()
        if not self.model.sellable:
            self.quantity.set_sensitive(False)
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    def update_visual_mode(self):
        for widget in [self.toggle_status_btn,
                       self.category_create, self.sellable_desc,
                       self.equip_search_button, self.quantity]:
            widget.set_sensitive(False)

    #
    #  Public API
    #

    def add_extra_tab(self, tab_label, slave):
        """Adds an extra tab to the editor

        :param tab_label: the label that will be display on the tab
        :param slave: the slave that will be attached to the new tab
        """
        event_box = gtk.EventBox()
        self.slaves_notebook.append_page(event_box, gtk.Label(tab_label))
        self.attach_slave(tab_label, slave, event_box)
        event_box.show()

    #
    #  Private
    #

    def _setup_widgets(self):
        # When editing an existing opened order, go to the quote tab.
        # But if the work is approved or in progress, go to execution tab.
        if self.model.status == WorkOrder.STATUS_OPENED and self.edit_mode:
            self._set_current_tab('quote_holder')
        elif self.model.status in [WorkOrder.STATUS_WORK_IN_PROGRESS,
                                   WorkOrder.STATUS_WORK_FINISHED,
                                   WorkOrder.STATUS_WORK_WAITING,
                                   WorkOrder.STATUS_DELIVERED]:
            self._set_current_tab('execution_holder')

        if self.edit_mode and self.model.sale:
            for widget in [self.client, self.category, self.category_create]:
                widget.set_sensitive(False)

        self._update_sellable_desc()

    def _update_sellable_desc(self):
        sellable = self.model.sellable
        if sellable is None:
            return

        if sellable.code:
            desc = "%s - %s" % (sellable.code, sellable.description)
        else:
            desc = sellable.description

        self.sellable_desc.set_text(desc)
        self.sellable_desc.set_tooltip_text(desc)

    def _update_view(self):
        self.proxy.update('status_str')

        # Cache this to avoid multiple queries
        has_open_inventory = bool(Inventory.has_open(
            self.store, api.get_current_branch(self.store)))

        tab = self._get_tab('execution_holder')
        # If it's not opened, it's at least approved.
        # So, we can enable the execution slave
        tab.set_sensitive(
            self.model.status == WorkOrder.STATUS_WORK_IN_PROGRESS and
            not has_open_inventory and not self.visual_mode)

        has_items = bool(self.model.order_items.count())
        if self.model.can_approve():
            label = _("Approve")
        elif self.model.can_work() and not has_items:
            label = _("Start")
        elif self.model.can_work():
            label = _("Continue")
        elif self.model.can_pause():
            label = _("Pause")
        else:
            label = ''
        self.toggle_status_btn.set_label(label)
        self.toggle_status_btn.set_sensitive(not self.visual_mode and
                                             self.model.client is not None)
        self.toggle_status_btn.set_visible(bool(label))

        stock_id, tooltip = get_workorder_state_icon(self.model)
        if stock_id is not None:
            self.state_icon.set_from_stock(stock_id, gtk.ICON_SIZE_MENU)
            self.state_icon.set_visible(True)
            self.state_icon.set_tooltip_text(tooltip)
        else:
            self.state_icon.hide()

    def _get_tab_pagenum(self, holder_name):
        return self.slaves_notebook.page_num(getattr(self, holder_name))

    def _get_tab(self, holder_name):
        page_num = self._get_tab_pagenum(holder_name)
        return self.slaves_notebook.get_nth_page(page_num)

    def _set_current_tab(self, holder_name):
        page_num = self._get_tab_pagenum(holder_name)
        self.slaves_notebook.set_current_page(page_num)

    def _setup_client_widget(self):
        self.client_gadget = ClientEntryGadget(
            entry=self.client,
            store=self.store,
            initial_value=self.model.client,
            parent=self)

    def _fill_categories_combo(self):
        if self.categories_for_combo is not None:
            categories = self.store.find(WorkOrderCategory,
                                         In(WorkOrderCategory.name,
                                            self.categories_for_combo))
        else:
            categories = self.store.find(WorkOrderCategory)
        self.category.color_attribute = 'color'
        self.category.prefill(
            api.for_combo(categories, empty=_(u"No category")))

    def _run_category_editor(self, category=None):
        with api.new_store() as store:
            rv = run_dialog(WorkOrderCategoryEditor, self, store, category,
                            visual_mode=self.visual_mode)
        if rv:
            self._fill_categories_combo()
            self.category.select(self.store.fetch(rv))

    def _maybe_toggle_status(self):
        if self.model.can_approve():
            self.model.approve()
        elif self.model.can_work():
            self.model.work()
        elif self.model.can_pause():
            msg_text = _(u"This will pause the order. Are you sure?")
            rv = run_dialog(
                NoteEditor, self, self.store, model=Note(),
                message_text=msg_text, label_text=_(u"Reason"), mandatory=True)
            if not rv:
                return
            self.model.pause(reason=rv.notes)

        self._update_view()
        self.history_slave.update_items()

    #
    #  Callbacks
    #

    def after_client__content_changed(self, combo):
        if self.proxy:
            self._update_view()

    def on_category__content_changed(self, combo):
        has_category = bool(combo.read())
        self.category_edit.set_sensitive(has_category)

    def on_category_create__clicked(self, button):
        self._run_category_editor()

    def on_category_edit__clicked(self, button):
        self._run_category_editor(category=self.category.read())

    def on_toggle_status_btn__clicked(self, button):
        self._maybe_toggle_status()

    def on_equip_search_button__clicked(self, button):
        ret = run_dialog(SellableSearch, self, self.store, hide_footer=True,
                         hide_toolbar=True, double_click_confirm=True,
                         show_closed_items=True)
        if not ret:
            return

        sellable = ret.sellable
        self.model.sellable = sellable
        self._update_sellable_desc()
        self.quantity.set_sensitive(True)


class WorkOrderPackageSendEditor(BaseEditor):
    """Editor responsible for creating and sending |workorderpackages|

    This will create a |workorderpackage|, add the |workorders| in it
    and mark it as sent on confirm.
    """

    size = (800, 400)
    model_name = _(u"Send work orders")
    model_type = WorkOrderPackage
    gladefile = 'WorkOrderPackageSendEditor'
    proxy_widgets = [
        'destination_branch',
        'identifier',
    ]

    #: The spec that will be used to populate the |workorders| to put in the
    #: |workorderpackage|. It must be a subclass of
    #: :class:`stoqlib.domain.workorder.WorkOrderView`
    #: or provide the same api it does.
    search_spec = WorkOrderApprovedAndFinishedView

    #
    #  BaseEditor
    #

    def create_model(self, store):
        # TODO: Add a parameter for getting a default destination branch
        return WorkOrderPackage(store=store, identifier=u'',
                                send_responsible=api.get_current_user(store),
                                source_branch=api.get_current_branch(store))

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model, self.proxy_widgets)

    def validate_confirm(self):
        if not any(i.will_send for i in self.workorders):
            warning(_(u"You need to select at least one work order"))
            return False

        return True

    def on_confirm(self):
        for order_view in self.workorders:
            if not order_view.will_send:
                continue
            # If note is false (that is, an empty string) pass None
            # to force the history's notes being set as null
            notes = order_view.notes if order_view.notes else None
            self.model.add_order(order_view.work_order, notes=notes)

        self.model.send()

    #
    #  Private
    #

    def _setup_widgets(self):
        self._prefill_branches()
        for widget in [self.details_btn, self.edit_btn]:
            widget.set_sensitive(False)

        self.workorders.set_columns([
            Column('will_send', _(u"Send"), data_type=bool, editable=True),
            IdentifierColumn('identifier', title=_('WO #'), sorted=True),
            IdentifierColumn('sale_identifier', title=_("Sale #"), visible=False),
            Column('status_str', _(u"Status"), data_type=str),
            Column('equipment', _(u"Equipment (Description)"), data_type=str,
                   expand=True, pack_end=True),
            Column('category_color', title=_(u'Equipment'),
                   column='equipment', data_type=gtk.gdk.Pixbuf,
                   format_func=render_pixbuf),
            Column('flag_icon', title=_(u'Equipment'), column='equipment',
                   data_type=gtk.gdk.Pixbuf, format_func_data=True,
                   format_func=self._format_state_icon),
            Column('branch_name', _(u"Branch"), data_type=str, visible=False),
            Column('client_name', _(u"Client"), data_type=str),
            Column('salesperson_name', _(u"Salesperson"), data_type=str,
                   visible=False),
            Column('open_date', _(u"Open date"),
                   data_type=datetime.date, visible=False),
            Column('approve_date', _(u"Approval date"),
                   data_type=datetime.date)])

        self._refresh_workorders()

    def _refresh_workorders(self):
        self.workorders.add_list(list(self._find_workorders()), clear=True)

    def _format_state_icon(self, item, data):
        stock_id, tooltip = get_workorder_state_icon(item.work_order)
        if stock_id is not None:
            # We are using self.identifier because render_icon is a
            # gtk.Widget's # method. It has nothing to do with results tough.
            return self.identifier.render_icon(stock_id, gtk.ICON_SIZE_MENU)

    def _find_workorders(self):
        current_branch = api.get_current_branch(self.store)
        destination_branch = self.destination_branch.get_selected()
        if destination_branch is None:
            return

        workorders = self.search_spec.find_by_can_send_to_branch(
            self.store, current_branch=current_branch,
            destination_branch=destination_branch)

        for workorder in workorders.order_by(self.search_spec.identifier):
            workorder.notes = u''
            workorder.will_send = False
            yield workorder

    def _prefill_branches(self):
        branches = Branch.get_active_remote_branches(self.store)
        current_branch = api.get_current_branch(self.store)

        # Branches not allowed to execute foreign work orders can only send
        # orders for those who can
        if not current_branch.can_execute_foreign_work_orders:
            branches = branches.find(can_execute_foreign_work_orders=True)

        self.destination_branch.prefill(api.for_person_combo(branches))

    def _edit_order(self, order_view):
        run_dialog(NoteEditor, self, self.store, model=order_view,
                   attr_name='notes', title=_(u"Notes"))

    #
    #  Callbacks
    #

    def on_destination_branch__content_changed(self, branches):
        self._refresh_workorders()

    def on_workorders__cell_edited(self, klist, obj, attr):
        self.force_validation()

    def on_workorders__selection_changed(self, workorders, selected):
        self.details_btn.set_sensitive(bool(selected))
        self.edit_btn.set_sensitive(bool(selected and selected.will_send))

    def on_workorders__row_activated(self, workorders, selected):
        if not self.edit_btn.get_sensitive():
            return

        selected = self.workorders.get_selected()
        self._edit_order(selected)

    def on_edit_btn__clicked(self, button):
        selected = self.workorders.get_selected()
        self._edit_order(selected)

    def on_details_btn__clicked(self, button):
        model = self.workorders.get_selected().work_order
        run_dialog(WorkOrderEditor, self, self.store,
                   model=model, visual_mode=True)
