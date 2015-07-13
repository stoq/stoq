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
from kiwi.ui.objectlist import Column
from kiwi.ui.gadgets import render_pixbuf

from stoqlib.database.runtime import get_current_branch, get_current_user
from stoqlib.domain.workorder import (WorkOrderPackage,
                                      WorkOrderPackageSentView,
                                      WorkOrderWithPackageView)
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.wizards import (BaseWizardStep, WizardEditorStep,
                                      BaseWizard)
from stoqlib.gui.editors.workordereditor import WorkOrderEditor
from stoqlib.gui.search.searchcolumns import IdentifierColumn
from stoqlib.gui.utils.workorderutils import get_workorder_state_icon

_ = stoqlib_gettext


#
#  Steps
#


class WorkOrderPackageReceiveSelectionStep(BaseWizardStep):
    """Step responsible for selecting a |workorderpackage| to receive"""

    gladefile = 'WorkOrderPackageReceiveSelectionStep'

    #
    #  WizardEditorStep
    #

    def post_init(self):
        self.packages.set_columns([
            Column('identifier', _(u"Package"), data_type=str, width=60),
            Column('source_branch_name', _(u"Source"), data_type=str, expand=True),
            Column('send_date', _(u"Send date"), data_type=datetime.date),
            Column('quantity', _(u"Quantity"), data_type=int)])
        self.packages.add_list(self._find_packages())

    def validate_step(self):
        if self.packages.get_selected() is None:
            warning(_(u"You need to select a package to receive first."))
            return False

        return True

    def next_step(self):
        selection = self.packages.get_selected()
        self.wizard.model = selection.package
        return WorkOrderPackageReceiveOrdersStep(
            self.store, self.wizard, model=self.wizard.model, previous=self)

    def has_next_step(self):
        return True

    #
    #  Private
    #

    def _find_packages(self):
        packages = WorkOrderPackageSentView.find_by_destination_branch(
            self.store, branch=get_current_branch(self.store))
        return packages.order_by(WorkOrderPackageSentView.identifier)


class WorkOrderPackageReceiveOrdersStep(WizardEditorStep):
    """Used to show what |workorders| are inside the |workorderpackage|

    Right now this step doesn't do much. It'll show all orders
    inside the package that are going to be received together with it.
    """

    model_type = WorkOrderPackage
    gladefile = 'WorkOrderPackageReceiveOrdersStep'
    proxy_widgets = [
        'identifier',
    ]

    #
    #  WizardEditorStep
    #

    def setup_proxies(self):
        self.details_btn.set_sensitive(False)

        self.workorders.set_columns([
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
            Column('client_name', _(u"Client"), data_type=str),
            Column('salesperson_name', _(u"Salesperson"), data_type=str,
                   visible=False),
            Column('open_date', _(u"Open date"),
                   data_type=datetime.date, visible=False),
            Column('approve_date', _(u"Approval date"),
                   data_type=datetime.date)])
        # Clear first to avoid duplication if the users goes back on the wizard
        self.workorders.clear()
        self.workorders.extend(self._find_orders())

        self.add_proxy(self.model, self.proxy_widgets)

    def has_next_step(self):
        return False

    #
    #  Private
    #

    def _format_state_icon(self, item, data):
        stock_id, tooltip = get_workorder_state_icon(item.work_order)
        if stock_id is not None:
            # We are using self.identifier because render_icon is a
            # gtk.Widget's # method. It has nothing to do with results tough.
            return self.identifier.render_icon(stock_id, gtk.ICON_SIZE_MENU)

    def _find_orders(self):
        orders = WorkOrderWithPackageView.find_by_package(
            store=self.store, package=self.model)
        return orders.order_by(WorkOrderWithPackageView.identifier)

    #
    #  Callbacks
    #

    def on_workorders__selection_changed(self, workorders, selected):
        self.details_btn.set_sensitive(bool(selected))

    def on_details_btn__clicked(self, button):
        model = self.workorders.get_selected().work_order
        run_dialog(WorkOrderEditor, self, self.store,
                   model=model, visual_mode=True)


#
#  Wizards
#


class WorkOrderPackageReceiveWizard(BaseWizard):
    """Wizard responsible for receiving |workorderpackages|

    This will mark the selected package as received on finish
    """

    title = _(u"Receive work orders")
    size = (800, 350)

    def __init__(self, store):
        first_step = WorkOrderPackageReceiveSelectionStep(store, wizard=self)
        super(WorkOrderPackageReceiveWizard, self).__init__(
            store, first_step=first_step)

    #
    #  BaseWizard
    #

    def finish(self):
        self.model.receive_responsible = get_current_user(self.store)
        self.model.receive()
        self.retval = self.model
        self.close()
