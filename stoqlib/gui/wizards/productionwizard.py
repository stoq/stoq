# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
""" Production wizard definition """

from decimal import Decimal

from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.ui.objectlist import Column
from storm.expr import And

from stoqlib.api import api
from stoqlib.domain.person import Branch, Employee
from stoqlib.domain.production import (ProductionOrder, ProductionItem,
                                       ProductionService)
from stoqlib.domain.service import ServiceView
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.views import ProductComponentView
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.formatters import format_quantity
from stoqlib.gui.base.wizards import (WizardEditorStep, BaseWizard,
                                      BaseWizardStep)
from stoqlib.gui.editors.productioneditor import (ProductionItemEditor,
                                                  ProductionServiceEditor)
from stoqlib.gui.slaves.productionslave import ProductionMaterialListSlave
from stoqlib.gui.wizards.abstractwizard import SellableItemStep

_ = stoqlib_gettext


#
# Wizard Steps
#


class OpenProductionOrderStep(WizardEditorStep):
    gladefile = 'OpenProductionOrderStep'
    model_type = ProductionOrder
    proxy_widgets = ['open_date',
                     'expected_start_date',
                     'identifier',
                     'branch',
                     'responsible',
                     'description']

    def __init__(self, store, wizard, model):
        WizardEditorStep.__init__(self, store, wizard, model)

    def _fill_branch_combo(self):
        branches = Branch.get_active_branches(self.store)
        self.branch.prefill(api.for_person_combo(branches))
        sync_mode = api.sysparam.get_bool('SYNCHRONIZED_MODE')
        self.branch.set_sensitive(not sync_mode)

    def _fill_responsible_combo(self):
        employees = self.store.find(Employee, status=Employee.STATUS_NORMAL)
        self.responsible.prefill(api.for_person_combo(employees))

    def _setup_widgets(self):
        self._fill_branch_combo()
        self._fill_responsible_combo()
        self.open_date.set_sensitive(False)

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.description.grab_focus()
        self.table.set_focus_chain([self.branch, self.expected_start_date,
                                    self.responsible, self.description])
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def next_step(self):
        return ProductionServiceStep(self.wizard, self, self.store, self.model)

    def has_previous_step(self):
        return False

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(
            self.model, OpenProductionOrderStep.proxy_widgets)
        self.proxy.update('identifier', unicode(self.model.identifier))
        # suggests a responsible for the production order
        if not self.model.responsible:
            self.responsible.select_item_by_position(0)

    #
    # Kiwi Callbacks
    #

    def on_expected_start_date__validate(self, widget, value):
        today = localtoday().date()
        if value and value < today:
            return ValidationError(
                _(u'Expected start date should be a future date.'))


class ProductionServiceStep(SellableItemStep):
    model_type = ProductionOrder
    item_table = ProductionService
    summary_label_text = "<b>%s</b>" % api.escape(_('Total:'))
    summary_label_column = 'quantity'
    sellable_view = ServiceView
    item_editor = ProductionServiceEditor

    #
    # Helper methods
    #

    def get_sellable_view_query(self):
        delivery_sellable = sysparam.get_object(
            self.store, 'DELIVERY_SERVICE').sellable

        query = And(ServiceView.status == Sellable.STATUS_AVAILABLE,
                    ServiceView.id != delivery_sellable.id)
        return self.sellable_view, query

    def setup_slaves(self):
        SellableItemStep.setup_slaves(self)
        self.item_lbl.set_text(_(u'Services:'))
        self.hide_add_button()
        self.cost_label.hide()
        self.cost.hide()

    def _get_production_service_by_sellable(self, sellable):
        service = sellable.service
        for item in self.slave.klist:
            if item.service is service:
                return item

    #
    # SellableItemStep virtual methods
    #

    def validate(self, value):
        # This step is optional
        self.wizard.refresh_next(value)

    def get_order_item(self, sellable, cost, quantity, batch=None, parent=None):
        assert batch is None
        item = self._get_production_service_by_sellable(sellable)
        if item is None:
            return ProductionService(service=sellable.service,
                                     quantity=quantity,
                                     order=self.model,
                                     store=self.store)
        item.quantity += quantity
        return item

    def get_saved_items(self):
        return list(self.model.get_service_items())

    def get_columns(self):
        return [
            Column('service.sellable.code', title=_('Code'), data_type=str),
            Column('service.sellable.category_description', title=_('Category'),
                   data_type=str, expand=True),
            Column('service.sellable.description', title=_('Description'),
                   data_type=str, expand=True, sorted=True),
            Column('quantity', title=_('Quantity'), data_type=Decimal,
                   format_func=format_quantity),
            Column('service.sellable.unit_description', title=_('Unit'),
                   data_type=str),
            Column('service.sellable.cost', title=_('Cost'),
                   data_type=currency)]

    def remove_items(self, items):
        for item in items:
            self.model.remove_service_item(item)

    #
    # WizardStep hooks
    #

    def next_step(self):
        return ProductionItemStep(self.wizard, self, self.store, self.model)


class ProductionItemStep(SellableItemStep):
    """ Wizard step for production items selection """
    model_type = ProductionOrder
    item_table = ProductionItem
    summary_label_text = "<b>%s</b>" % (api.escape(_('Total:')),)
    summary_label_column = 'quantity'
    sellable_view = ProductComponentView
    item_editor = ProductionItemEditor

    #
    # Helper methods
    #

    def get_sellable_view_query(self):
        return self.sellable_view, None

    def setup_slaves(self):
        SellableItemStep.setup_slaves(self)
        self.hide_add_button()
        self.cost_label.hide()
        self.cost.hide()

    def _get_production_item_by_sellable(self, sellable):
        product = sellable.product
        for item in self.slave.klist:
            if item.product is product:
                return item

    #
    # SellableItemStep virtual methods
    #

    def get_order_item(self, sellable, cost, quantity, batch=None, parent=None):
        # We should not add the children to the list
        if parent:
            return
        # We are not allowing production items to control batches right now
        assert batch is None
        item = self._get_production_item_by_sellable(sellable)
        if item is None:
            return self.model.add_item(sellable, quantity)

        item.quantity += quantity
        return item

    def get_saved_items(self):
        return list(self.model.get_items())

    def get_columns(self):
        return [
            Column('product.sellable.code', title=_('Code'), data_type=str),
            Column('product.sellable.category_description', title=_('Category'),
                   data_type=str, expand=True),
            Column('product.sellable.description', title=_('Description'),
                   data_type=str, expand=True, sorted=True),
            Column('quantity', title=_('Quantity'), data_type=Decimal,
                   format_func=format_quantity),
            Column('product.sellable.unit_description', title=_('Unit'),
                   data_type=str)]

    #
    # WizardStep hooks
    #

    def next_step(self):
        return FinishOpenProductionOrderStep(self.wizard, self, self.store,
                                             self.model)


class FinishOpenProductionOrderStep(BaseWizardStep):
    gladefile = 'HolderTemplate'
    model_type = ProductionOrder
    proxy_widgets = []

    def __init__(self, wizard, previous, store, model):
        self._order = model
        BaseWizardStep.__init__(self, store, wizard, previous)
        self._setup_slaves()

    def _setup_slaves(self):
        self._slave = ProductionMaterialListSlave(self.store, self._order,
                                                  visual_mode=True)
        self.attach_slave('place_holder', self._slave)
    #
    # WizardStep hooks
    #

    def has_next_step(self):
        return False

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()
        # Reload materials, so if we go back and forward, the materials are
        # updated properly,
        self._slave.reload_materials()

    def validate_step(self):
        return self._slave.validate_confirm()

#
# Main wizard
#


class ProductionWizard(BaseWizard):
    size = (775, 400)

    def __init__(self, store, model=None, edit_mode=False):
        title = self._get_title(model)
        model = model or self._create_model(store)
        first_step = OpenProductionOrderStep(store, self, model)
        BaseWizard.__init__(self, store, first_step, model, title=title,
                            edit_mode=edit_mode)

    def _get_title(self, model=None):
        if not model:
            return _(u'New Production')
        return _(u'Edit Production')

    def _create_model(self, store):
        branch = api.get_current_branch(store)
        return ProductionOrder(branch=branch,
                               store=store)

    #
    # WizardStep hooks
    #

    def finish(self):
        self.retval = self.model
        self.close()
