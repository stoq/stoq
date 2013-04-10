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

import gtk

from stoqlib.api import api
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.slaves.workorderslave import (WorkOrderOpeningSlave,
                                               WorkOrderQuoteSlave,
                                               WorkOrderExecutionSlave)
from stoqlib.domain.person import Client
from stoqlib.domain.workorder import WorkOrder, WorkOrderCategory
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.personeditor import ClientEditor
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.gui.editors.workordercategoryeditor import WorkOrderCategoryEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class WorkOrderEditor(BaseEditor):
    """An editor for working with |workorder| objects"""

    size = (800, 500)
    gladefile = 'WorkOrderEditor'
    model_type = WorkOrder
    model_name = _(u'Work order')
    help_section = 'workorder'
    proxy_widgets = [
        'category',
        'client',
        'equipment',
        'identifier',
        'status_str',
    ]

    def __init__(self, store, model=None, visual_mode=False, category=None):
        self._default_category = category
        super(WorkOrderEditor, self).__init__(store, model=model,
                                              visual_mode=visual_mode)

    #
    #  BaseEditor
    #

    def create_model(self, store):
        branch = api.get_current_branch(store)
        return WorkOrder(
            store=store,
            equipment=u'',
            branch=branch,
            category=self._default_category,
        )

    def setup_slaves(self):
        self.opening_slave = WorkOrderOpeningSlave(
            self.store, self.model, visual_mode=self.visual_mode)
        self.attach_slave('opening_holder', self.opening_slave)

        self.quote_slave = WorkOrderQuoteSlave(
            self.store, self.model, visual_mode=self.visual_mode)
        self.attach_slave('quote_holder', self.quote_slave)

        self.execution_slave = WorkOrderExecutionSlave(
            self.store, self.model, visual_mode=self.visual_mode)
        self.attach_slave('execution_holder', self.execution_slave)
        # FIXME: It's strange to connect to the list on a slave on other slave
        # and other slave, but we need to update status_str proxy after.
        # Is there a way of doing this without having to create a gsinal
        # in each slave and propagate one to another?
        self.execution_slave.sellable_item_slave.slave.klist.connect(
            'has-rows', self._on_execution_slave__has_rows)

        self._update_view()

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    def update_visual_mode(self):
        for widget in [self.has_client_approval, self.client_create,
                       self.category_create]:
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
        for widget in [self.client_edit, self.category_edit]:
            widget.set_sensitive(False)
        self._fill_clients_combo()
        self._fill_categories_combo()

        # When editing an existing opened order, go to the quote tab.
        # But if the work is approved or in progress, go to execution tab.
        if self.model.status == WorkOrder.STATUS_OPENED and self.edit_mode:
            self._set_current_tab('quote_holder')
        elif self.model.status in [WorkOrder.STATUS_WORK_IN_PROGRESS,
                                   WorkOrder.STATUS_WORK_FINISHED,
                                   WorkOrder.STATUS_CLOSED,
                                   WorkOrder.STATUS_APPROVED]:
            self._set_current_tab('execution_holder')

    def _update_view(self):
        self.proxy.update('status_str')

        is_approved = self.model.status != WorkOrder.STATUS_OPENED
        # If it's not opened, it's at least approved.
        # So, we can enable the execution slave
        tab = self._get_tab('execution_holder')
        tab.set_sensitive(is_approved)

        if is_approved and not self.has_client_approval.get_active():
            self.has_client_approval.set_active(True)

        # Once we started working, it makes no sense to
        # remove client's approval
        if self.model.status == WorkOrder.STATUS_WORK_IN_PROGRESS:
            self.has_client_approval.set_sensitive(False)
        else:
            has_client = self.model.client is not None
            self.has_client_approval.set_sensitive(has_client and
                                                   not self.visual_mode)

    def _get_tab_pagenum(self, holder_name):
        return self.slaves_notebook.page_num(getattr(self, holder_name))

    def _get_tab(self, holder_name):
        page_num = self._get_tab_pagenum(holder_name)
        return self.slaves_notebook.get_nth_page(page_num)

    def _set_current_tab(self, holder_name):
        page_num = self._get_tab_pagenum(holder_name)
        self.slaves_notebook.set_current_page(page_num)

    def _fill_clients_combo(self):
        clients = Client.get_active_clients(self.store)
        self.client.prefill(api.for_person_combo(clients))

    def _fill_categories_combo(self):
        categories = self.store.find(WorkOrderCategory)
        self.category.prefill(
            api.for_combo(categories, empty=_(u"No category")))

    def _run_client_editor(self, client=None):
        with api.trans() as store:
            rv = run_person_role_dialog(ClientEditor, self, store, client,
                                        visual_mode=self.visual_mode)
        if rv:
            self._fill_clients_combo()
            self.client.select(self.store.fetch(rv))

    def _run_category_editor(self, category=None):
        with api.trans() as store:
            rv = run_dialog(WorkOrderCategoryEditor, self, store, category,
                            visual_mode=self.visual_mode)
        if rv:
            self._fill_categories_combo()
            self.category.select(self.store.fetch(rv))

    #
    #  Callbacks
    #

    def _on_execution_slave__has_rows(self, klist, has_rows):
        if has_rows and self.model.can_start():
            self.model.start()

        self._update_view()

    def on_client__content_changed(self, combo):
        has_client = bool(combo.read())
        self.client_edit.set_sensitive(has_client)

    def after_client__content_changed(self, combo):
        self._update_view()

    def on_category__content_changed(self, combo):
        has_category = bool(combo.read())
        self.category_edit.set_sensitive(has_category)

    def on_client_create__clicked(self, button):
        self._run_client_editor()

    def on_client_edit__clicked(self, button):
        self._run_client_editor(client=self.client.read())

    def on_category_create__clicked(self, button):
        self._run_category_editor()

    def on_category_edit__clicked(self, button):
        self._run_category_editor(category=self.category.read())

    def on_has_client_approval__toggled(self, check):
        if check.get_active() and self.model.can_approve():
            self.model.approve()
        if not check.get_active() and self.model.can_undo_approval():
            self.model.undo_approval()

        self._update_view()
