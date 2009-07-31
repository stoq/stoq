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
## Author(s):   George Kussumoto    <george@async.com.br>
##
""" Production wizard definition """

import datetime
from decimal import Decimal

import pango

from kiwi.datatypes import ValidationError, currency
from kiwi.ui.widgets.list import Column, ColoredColumn

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.interfaces import IBranch, IStorable
from stoqlib.domain.person import Person, PersonAdaptToEmployee
from stoqlib.domain.production import (ProductionOrder, ProductionItem,
                                       ProductionMaterial, ProductionService)
from stoqlib.domain.service import ServiceView
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.views import ProductComponentView
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.validators import format_quantity
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.editors.productioneditor import (ProductionItemEditor,
                                                  ProductionMaterialEditor,
                                                  ProductionServiceEditor)
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
                     'order_number',
                     'branch',
                     'responsible',
                     'description',]

    def __init__(self, conn, wizard, model):
        WizardEditorStep.__init__(self, conn, wizard, model)

    def _fill_branch_combo(self):
        # FIXME: Implement and use IDescribable on PersonAdaptToBranch
        table = Person.getAdapterClass(IBranch)
        branches = table.get_active_branches(self.conn)
        items = [(s.person.name, s) for s in branches]
        self.branch.prefill(sorted(items))

    def _fill_responsible_combo(self):
        employees = PersonAdaptToEmployee.selectBy(
            status=PersonAdaptToEmployee.STATUS_NORMAL,
            connection=self.conn)
        self.responsible.prefill([(e.person.name, e) for e in employees])

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
        return ProductionServiceStep(self.wizard, self, self.conn, self.model)

    def has_previous_step(self):
        return False

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(
            self.model, OpenProductionOrderStep.proxy_widgets)
        self.proxy.update('order_number', u'%04d' % self.model.id)
        # suggests a responsible for the production order
        self.responsible.select_item_by_position(0)

    #
    # Kiwi Callbacks
    #

    def on_expected_start_date__validate(self, widget, value):
        today = datetime.date.today()
        if value and value < today:
            return ValidationError(
                _(u'Expected start date should be a future date.'))


class ProductionServiceStep(SellableItemStep):
    model_type = ProductionOrder
    item_table = ProductionService
    summary_label_text = "<b>%s</b>" % _('Total:')
    summary_label_column = 'quantity'

    #
    # Helper methods
    #

    def setup_sellable_entry(self):
        max_results = sysparam(self.conn).MAX_SEARCH_RESULTS
        service_view_items = ServiceView.select(
            ServiceView.q.status == Sellable.STATUS_AVAILABLE,
            connection=self.conn,
            limit=max_results)
        delivery = sysparam(self.conn).DELIVERY_SERVICE
        self.sellable.prefill([(s.description, s.sellable)
            for s in service_view_items if s.id != delivery.id])

    def setup_slaves(self):
        SellableItemStep.setup_slaves(self)
        self.item_lbl.set_text(_(u'Services:'))
        self.hide_add_button()
        self.product_button.hide()
        self.cost_label.hide()
        self.cost.hide()

        self.quantity.connect('validate', self._on_quantity__validate)

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
        return True

    def get_order_item(self, sellable, cost, quantity):
        item = self._get_production_service_by_sellable(sellable)
        if item is None:
            return ProductionService(service=sellable.service,
                                     quantity=quantity,
                                     order=self.model,
                                     connection=self.conn)
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
            Column('service.sellable.unit_description',title=_('Unit'),
                    data_type=str),
            Column('service.sellable.cost', title=_('Cost'),
                    data_type=currency),]

    #
    # WizardStep hooks
    #

    def post_init(self):
        SellableItemStep.post_init(self)
        self.slave.set_editor(ProductionServiceEditor)

    def next_step(self):
        return ProductionItemStep(self.wizard, self, self.conn, self.model)

    #
    # Callbacks
    #

    def _on_quantity__validate(self, widget, value):
        if not value or value <= Decimal(0):
            return ValidationError(_(u'Quantity must be greater than zero'))


class ProductionItemStep(SellableItemStep):
    """ Wizard step for production items selection """
    model_type = ProductionOrder
    item_table = ProductionItem
    summary_label_text = "<b>%s</b>" % _('Total:')
    summary_label_column = 'quantity'

    #
    # Helper methods
    #

    def setup_sellable_entry(self):
        max_results = sysparam(self.conn).MAX_SEARCH_RESULTS
        composable_items = ProductComponentView.select(connection=self.conn,
                                                       limit=max_results)
        self.sellable.prefill(
            [(c.description, c.sellable) for c in composable_items])

    def setup_slaves(self):
        SellableItemStep.setup_slaves(self)
        self.hide_add_button()
        self.product_button.hide()
        self.cost_label.hide()
        self.cost.hide()

        self.quantity.connect('validate', self._on_quantity__validate)

    def _get_production_item_by_sellable(self, sellable):
        product = sellable.product
        for item in self.slave.klist:
            if item.product is product:
                return item

    #
    # SellableItemStep virtual methods
    #

    def get_order_item(self, sellable, cost, quantity):
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
            Column('product.sellable.unit_description',title=_('Unit'),
                    data_type=str),]

    #
    # WizardStep hooks
    #

    def post_init(self):
        SellableItemStep.post_init(self)
        self.slave.set_editor(ProductionItemEditor)

    def next_step(self):
        return FinishOpenProductionOrderStep(self.wizard, self, self.conn,
                                             self.model)

    #
    # Callbacks
    #

    def _on_quantity__validate(self, widget, value):
        if not value or value <= Decimal(0):
            return ValidationError(_(u'Quantity must be greater than zero'))


#XXX: This is just a workaround to avoid the zillions of queries
#     when handling production items and materials.
class _TemporaryMaterial(object):
    def __init__(self, production, component, conn):
        storable = IStorable(component, None)
        if storable is not None:
            self.stock_quantity =  storable.get_full_balance(production.branch)
        else:
            self.stock_quantity = 0

        sellable = component.sellable
        self.code = sellable.code
        self.description = sellable.get_description()
        self.category_description = sellable.get_description()
        self.unit_description = sellable.get_unit_description()
        self.product = component
        self.needed = 0
        self.to_purchase = 0
        self.to_make = 0
        self.order = production
        self._material = None
        self._conn = conn

    @property
    def material(self):
        if self._material is None:
            # At this point, the needed quantity have already been updated.
            assert self.needed > 0
            material = ProductionMaterial.selectOneBy(order=self.order,
                                                      product=self.product,
                                                      connection=self._conn)
            if material is not None:
                self._material = material
                self._material.needed = self.needed
            else:
                self._material = ProductionMaterial(
                                                needed=self.needed,
                                                to_purchase=self.to_purchase,
                                                to_make=self.to_make,
                                                order=self.order,
                                                product=self.product,
                                                connection=self._conn)
        return self._material

    def create(self):
        return self.material

    def sync(self):
        #assert self._material is not None
        self.to_purchase = self.material.to_purchase
        self.to_make = self.material.to_make

    def add_quantity(self, quantity):
        assert quantity > 0
        self.needed += quantity
        missing_quantity = self.needed - self.stock_quantity
        if missing_quantity > 0:
            if self.product.has_components():
                self.to_make = missing_quantity
            else:
                self.to_purchase = missing_quantity
        if self._material is not None:
            self._material.needed = self.needed
            self._material.to_make = self.to_make
            self._material.to_purchase = self.to_purchase


class FinishOpenProductionOrderStep(WizardEditorStep):
    gladefile = 'FinishOpenProductionOrderStep'
    model_type = ProductionOrder
    proxy_widgets = []

    def __init__(self, wizard, previous, conn, model):
        WizardEditorStep.__init__(self, conn, wizard, model, previous)
        self._setup_widgets()

    def _add_materials(self, production_item):
        self._materials_objects = []
        for product_component in production_item.get_components():
            material = self._get_or_create_material(product_component)
            quantity = product_component.quantity * production_item.quantity
            material.add_quantity(quantity)
            material.sync()

            if material not in self.materials:
                self.materials.append(material)
            else:
                self.materials.update(material)

    def _get_or_create_material(self, product_component):
        component = product_component.component
        for material in self.materials:
            if material.product is component:
                return material
        return _TemporaryMaterial(self.model, component, self.conn)

    def _edit_production_material(self):
        material = self.materials.get_selected()
        assert material is not None

        retval = run_dialog(ProductionMaterialEditor, self, self.conn,
                            material.material)
        if retval:
            material.sync()
            self.materials.update(material)

    def _setup_widgets(self):
        self.edit_button.set_sensitive(False)
        self.materials.set_columns(self._get_columns())
        for production_item in self.model.get_items():
            self._add_materials(production_item)

    def _get_columns(self):
        return [
            Column('code', title=_('Code'), data_type=str),
            Column('category_description', title=_('Category'),
                    data_type=str, expand=True, ellipsize=pango.ELLIPSIZE_END),
            Column('description', title=_('Description'), data_type=str,
                    expand=True, ellipsize=pango.ELLIPSIZE_END, sorted=True),
            Column('unit_description',title=_('Unit'),
                    data_type=str),
            Column('needed', title=_('Needed'), data_type=Decimal,
                    format_func=format_quantity),
            Column('stock_quantity', title=_('In Stock'), data_type=Decimal,
                    format_func=format_quantity),
            ColoredColumn('to_purchase', title=_('To Purchase'),
                          data_type=Decimal, format_func=format_quantity,
                          use_data_model=True, color='red',
                          data_func=self._colorize_to_purchase_col),
            ColoredColumn('to_make', title=_('To Make'), data_type=Decimal,
                          format_func=format_quantity, use_data_model=True,
                          color='red', data_func=self._colorize_to_make_col),]

    #XXX: Some duplication here, since the columns will never be both red.

    def _colorize_to_purchase_col(self, material):
        if material.product.has_components():
            return
        stock_qty = material.stock_quantity
        if material.to_purchase + stock_qty - material.needed < 0:
           return True
        return False

    def _colorize_to_make_col(self, material):
        if not material.product.has_components():
            return
        stock_qty = material.stock_quantity
        if material.to_make + stock_qty - material.needed < 0:
           return True
        return False

    #
    # WizardStep hooks
    #

    def has_next_step(self):
        return False

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    def validate_step(self):
        # Used as a hook for the finish button
        for material in self.materials:
            material.create()

        if self.start_production_check.get_active():
            self.model.start_production()
        elif self.model.status != ProductionOrder.ORDER_WAITING:
            for material in self.materials:
                if material.to_purchase > 0 or material.to_make > 0:
                    self.model.set_production_waiting()
                    break
        return True

    #
    # Kiwi Callbacks
    #

    def on_materials__selection_changed(self, widget, material):
        self.edit_button.set_sensitive(bool(material))

    def on_materials__double_click(self, widget, material):
        self._edit_production_material()

    def on_edit_button__clicked(self, widget):
        self._edit_production_material()


#
# Main wizard
#


class ProductionWizard(BaseWizard):
    size = (775, 400)

    def __init__(self, conn, model=None, edit_mode=False):
        title = self._get_title(model)
        model = model or self._create_model(conn)
        first_step = OpenProductionOrderStep(conn, self, model)
        BaseWizard.__init__(self, conn, first_step, model, title=title,
                            edit_mode=edit_mode)

    def _get_title(self, model=None):
        if not model:
            return _(u'New Production')
        return _(u'Edit Production')

    def _create_model(self, conn):
        branch = get_current_branch(conn)
        return ProductionOrder(branch=branch,
                               connection=conn)

    #
    # WizardStep hooks
    #

    def finish(self):
        self.retval = self.model
        self.close()
