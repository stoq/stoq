# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import collections
import decimal
import logging

from storm.expr import LeftJoin
from storm.info import ClassAlias


from stoqlib.api import api
from stoqlib.database.runtime import get_default_store
from stoqlib.database.viewable import Viewable
from stoqlib.domain.events import WorkOrderStatusChangedEvent
from stoqlib.domain.product import Product, ProductManufacturer
from stoqlib.domain.person import Person
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.workorder import WorkOrder
from stoq.lib.gui.actions.base import BaseActions, action
from stoq.lib.gui.actions.workorder import WorkOrderActions
from stoq.lib.gui.base.dialogs import run_dialog
from stoq.lib.gui.editors.personeditor import ClientEditor
from stoq.lib.gui.editors.producteditor import ProductEditor
from stoq.lib.gui.editors.workordereditor import WorkOrderEditor
from stoq.lib.gui.events import (StartApplicationEvent, EditorCreateEvent, RunDialogEvent,
                                 PrintReportEvent, SearchDialogSetupSearchEvent,
                                 ApplicationSetupSearchEvent)
from stoq.lib.gui.search.searchcolumns import SearchColumn
from stoq.lib.gui.search.searchextension import SearchExtension
from stoq.lib.gui.utils.keybindings import add_bindings, get_accels
from stoq.lib.gui.utils.printing import print_report
from stoq.lib.gui.widgets.workorder import WorkOrderRow
from stoq.lib.gui.wizards.personwizard import PersonRoleWizard
from stoq.lib.gui.wizards.workorderquotewizard import WorkOrderQuoteWizard
from stoqlib.lib.message import warning
from stoqlib.lib.parameters import ParameterDetails, sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.sale import SaleOrderReport

from stoq.gui.services import ServicesApp

from .medicssearch import OpticalMedicSearch, MedicSalesSearch
from .opticaleditor import MedicEditor, OpticalWorkOrderEditor, OpticalSupplierEditor
from .opticalhistory import OpticalPatientDetails
from .opticalreport import OpticalWorkOrderReceiptReport
from .opticalslave import ProductOpticSlave, WorkOrderOpticalSlave
from .opticalwizard import OpticalSaleQuoteWizard, MedicRoleWizard
from .opticaldomain import OpticalProduct, OpticalWorkOrder, OpticalMedic


_ = stoqlib_gettext
log = logging.getLogger(__name__)


class ProductSearchExtention(SearchExtension):
    spec_attributes = collections.OrderedDict([
        ('gf_glass_type', OpticalProduct.gf_glass_type),
        ('gf_size', OpticalProduct.gf_size),
        ('gf_lens_type', OpticalProduct.gf_lens_type),
        ('gf_color', OpticalProduct.gf_color),
        ('gl_photosensitive', OpticalProduct.gl_photosensitive),
        ('gl_anti_glare', OpticalProduct.gl_anti_glare),
        ('gl_refraction_index', OpticalProduct.gl_refraction_index),
        ('gl_classification', OpticalProduct.gl_classification),
        ('gl_addition', OpticalProduct.gl_addition),
        ('gl_diameter', OpticalProduct.gl_diameter),
        ('gl_height', OpticalProduct.gl_height),
        ('gl_availability', OpticalProduct.gl_availability),
        ('cl_degree', OpticalProduct.cl_degree),
        ('cl_classification', OpticalProduct.cl_classification),
        ('cl_lens_type', OpticalProduct.cl_lens_type),
        ('cl_discard', OpticalProduct.cl_discard),
        ('cl_addition', OpticalProduct.cl_addition),
        ('cl_cylindrical', OpticalProduct.cl_cylindrical),
        ('cl_axis', OpticalProduct.cl_axis),
        ('cl_color', OpticalProduct.cl_color),
        ('cl_curvature', OpticalProduct.cl_curvature),
    ])
    spec_joins = [
        LeftJoin(OpticalProduct, OpticalProduct.product_id == Product.id)
    ]

    def get_columns(self):
        info_cols = collections.OrderedDict([
            (_('Frame'), [
                ('gf_glass_type', _('Glass Type'), str, False),
                ('gf_size', _('Size'), str, False),
                ('gf_lens_type', _('Lens Type'), str, False),
                ('gf_color', _('Color'), str, False),
            ]),
            (_('Glass Lenses'), [
                ('gl_photosensitive', _('Photosensitive'), str, False),
                ('gl_anti_glare', _('Anti Glare'), str, False),
                ('gl_refraction_index', _('Refraction Index'), str, False),
                ('gl_classification', _('Classification'), str, False),
                ('gl_addition', _('Addition'), str, False),
                ('gl_diameter', _('Diameter'), str, False),
                ('gl_height', _('Height'), str, False),
                ('gl_availability', _('Availability'), str, False),
            ]),
            (_('Contact Lenses'), [
                ('cl_degree', _('Degree'), decimal.Decimal, False),
                ('cl_classification', _('Classification'), str, False),
                ('cl_lens_type', _('Lens Type'), str, False),
                ('cl_discard', _('Discard'), str, False),
                ('cl_addition', _('Addition'), str, False),
                ('cl_cylindrical', _('Cylindrical'), decimal.Decimal, False),
                ('cl_axis', _('Axis'), decimal.Decimal, False),
                ('cl_color', _('Color'), str, False),
                ('cl_curvature', _('Curvature'), str, False),
            ]),
        ])

        columns = []
        for label, columns_list in info_cols.items():
            for c in columns_list:
                columns.append(
                    SearchColumn(c[0], title='%s - %s' % (label, c[1]),
                                 data_type=c[2], visible=c[3]))
        return columns


class ServicesSearchExtention(SearchExtension):
    PersonMedic = ClassAlias(Person, 'person_medic')

    spec_attributes = dict(
        manufacturer_name=ProductManufacturer.name,
        medic_name=PersonMedic.name,
    )
    spec_joins = [
        LeftJoin(Product, Product.id == Sellable.id),
        LeftJoin(ProductManufacturer,
                 Product.manufacturer_id == ProductManufacturer.id),
        LeftJoin(OpticalWorkOrder, OpticalWorkOrder.work_order_id == WorkOrder.id),
        LeftJoin(OpticalMedic, OpticalWorkOrder.medic_id == OpticalMedic.id),
        LeftJoin(PersonMedic, PersonMedic.id == OpticalMedic.person_id),
    ]

    def get_columns(self):
        return [
            SearchColumn('manufacturer_name', title=_('Manufacturer'), data_type=str,
                         visible=False),
            SearchColumn('medic_name', title=_('Medic'), data_type=str, visible=False),
        ]


class OpticalWorkOrderActions(BaseActions):
    group_name = 'optical_work_order'

    def set_model(self, model):
        self.model = model
        optical_wo = model and OpticalWorkOrder.find_by_work_order(model.store, model)
        self.set_action_enabled('OpticalDetails', bool(optical_wo))
        self.set_action_enabled('OpticalNewPurchase',
                                optical_wo and optical_wo.can_create_purchase())

    @action('OpticalDetails')
    def optical_details(self, work_order):
        with api.new_store() as store:
            work_order = store.fetch(work_order)
            run_dialog(OpticalWorkOrderEditor, None, store, work_order)

    @action('OpticalNewPurchase')
    def optical_new_purchase(self, work_order):
        with api.new_store() as store:
            order = store.fetch(work_order)
            rv = run_dialog(OpticalSupplierEditor, None, store, order)
            if not rv:
                return False

            order.supplier_order = rv.supplier_order
            optical_wo = OpticalWorkOrder.find_by_work_order(store, order)
            optical_wo.create_purchase(rv.supplier, rv.item, rv.is_freebie,
                                       api.get_current_branch(store),
                                       api.get_current_station(store), api.get_current_user(store))


params = [
    ParameterDetails(
        u'CUSTOM_WORK_ORDER_DESCRIPTION',
        _(u'Work order'),
        _(u'Allow to customize the work order description'),
        _(u'If true, it will be allowed to set a description for the work order '
          u'manually. Otherwise, the identifier will be used.'),
        bool, initial=True)
]


class OpticalUI(object):
    def __init__(self):
        self._setup_params()
        self.default_store = get_default_store()
        StartApplicationEvent.connect(self._on_StartApplicationEvent)
        EditorCreateEvent.connect(self._on_EditorCreateEvent)
        RunDialogEvent.connect(self._on_RunDialogEvent)
        PrintReportEvent.connect(self._on_PrintReportEvent)
        SearchDialogSetupSearchEvent.connect(self._on_SearchDialogSetupSearchEvent)
        WorkOrderStatusChangedEvent.connect(self._on_WorkOrderStatusChangedEvent)
        ApplicationSetupSearchEvent.connect(self._on_ApplicationSetupSearchEvent)

        add_bindings([
            ('plugin.optical.pre_sale', ''),
            ('plugin.optical.search_medics', ''),
        ])

        # Whenever the model of WorkOrderActions change, we should also change ours
        actions = WorkOrderActions.get_instance()
        actions.connect('model-set', self._on_work_order_actions__model_set)

        # Add a new option to the WorkOrderRow options menu
        WorkOrderRow.options.append((_('Create new purchase...'),
                                     'optical_work_order.OpticalNewPurchase'))

    def _on_work_order_actions__model_set(self, actions, model):
        OpticalWorkOrderActions.get_instance().set_model(model)

    @classmethod
    def get_instance(cls):
        if hasattr(cls, '_instance'):
            return cls._instance

        cls._instance = cls()
        return cls._instance

    #
    # Private
    #

    def _setup_params(self):
        for detail in params:
            sysparam.register_param(detail)

    def _add_sale_menus(self, sale_app):
        group = get_accels('plugin.optical')
        actions = [
            ('OpticalMenu', None, _(u'Optical')),
            ('OpticalPreSale', None, _(u'Sale with work order...'),
             group.get('pre_sale'), None,
             self._on_OpticalPreSale__activate),
            ('OpticalMedicSearch', None, _(u'Medics...'),
             group.get('search_medics'), None,
             self._on_MedicsSearch__activate),
            ('OpticalMedicSaleItems', None, _(u'Medics sold items...'),
             None, None,
             self._on_MedicSaleItems__activate),
        ]
        sale_app.add_ui_actions(actions)

        # XXX: Is this really necessary? Looks the same as the regular sale with
        # work order
        #sale_app.window.add_new_items([sale_app.OpticalPreSale])

        sale_app.window.add_search_items([
            sale_app.OpticalMedicSearch,
            sale_app.OpticalMedicSaleItems,
        ], _('Optical'))

    def _add_services_menus(self, services_app):
        services_app.window.add_extra_items2([
            (_(u'Edit optical details...'), 'optical_work_order.OpticalDetails'),
        ], _('Optical'))

        options = services_app.get_domain_options()
        options.append(('', _('Edit optical details...'), 'optical_work_order.OpticalDetails',
                        False))
        options.append(('', _('Create new purchase...'), 'optical_work_order.OpticalNewPurchase',
                        False))
        # Recreate the app popover with the new options
        services_app.create_popover(options)

    def _fix_work_order_editor(self, editor, model, store):
        from gi.repository import Gtk

        slave = WorkOrderOpticalSlave(store, model, show_finish_date=False,
                                      visual_mode=editor.visual_mode, parent=editor)
        editor.add_extra_tab('Ótico', slave)

        def _print_report(button):
            print_report(OpticalWorkOrderReceiptReport, [model])

        # Also add an print button
        if editor.edit_mode:
            print_button = editor.add_button(_('Print'), Gtk.STOCK_PRINT)
            print_button.connect('clicked', _print_report)

    def _add_product_slave(self, editor, model, store):
        editor.add_extra_tab(ProductOpticSlave.title,
                             ProductOpticSlave(store, model))

    def _create_pre_sale(self):
        if self._current_app.check_open_inventory():
            warning(_("You cannot create a pre-sale with an open inventory."))
            return

        with api.new_store() as store:
            run_dialog(OpticalSaleQuoteWizard, self._current_app, store)

        if store.committed:
            self._current_app.refresh()

    def _add_patient_history_button(self, editor, model):
        button = editor.add_button(_(u'Patient History'))
        button.connect('clicked', self._on_patient_history_clicked, editor, model)

        # Save the button on the editor, so the tests can click on it
        editor.patient_history_button = button

    #
    # Events
    #

    def _on_StartApplicationEvent(self, appname, app):
        self._current_app = app
        if appname == 'sales':
            self._add_sale_menus(app)
        elif appname == 'services':
            self._add_services_menus(app)

    def _on_EditorCreateEvent(self, editor, model, store, *args):
        # Use type() instead of isinstance so tab does not appear on subclasses
        # (unless thats the desired effect)
        editor_type = type(editor)
        if editor_type is ProductEditor:
            self._add_product_slave(editor, model, store)
        elif editor_type is WorkOrderEditor:
            self._fix_work_order_editor(editor, model, store)
        elif editor_type is ClientEditor:
            self._add_patient_history_button(editor, model)

    def _on_RunDialogEvent(self, dialog, parent, *args, **kwargs):
        # Every sale with work order should use OpticalSaleQuoteWizard instead
        # of WorkOrderQuoteWizard when this plugin is enabled
        if dialog is WorkOrderQuoteWizard:
            return OpticalSaleQuoteWizard
        elif dialog is PersonRoleWizard and MedicEditor in args:
            return MedicRoleWizard

    def _on_SearchDialogSetupSearchEvent(self, dialog):
        if not issubclass(dialog.search_spec, Viewable):
            return
        viewable = dialog.search_spec
        if (viewable.has_column(Sellable.description) and
                viewable.has_join_with(Product)):
            dialog.add_extension(ProductSearchExtention())

    def _on_ApplicationSetupSearchEvent(self, app):
        if isinstance(app, ServicesApp):
            extention = ServicesSearchExtention()
            extention.attach(app)

    def _on_WorkOrderStatusChangedEvent(self, order, old_status):
        if old_status == WorkOrder.STATUS_OPENED:
            #Do nothing at this point.
            return

        optical_wo = OpticalWorkOrder.find_by_work_order(order.store, order)
        # If there is no optical WO, nothing to do here
        if optical_wo is None:
            return

        if optical_wo.can_create_purchase():
            with api.new_store() as store:
                rv = run_dialog(OpticalSupplierEditor, None, store, order)
            if not rv:
                # Return None to let the status be changed without creating a purchase order
                return

            order.supplier_order = rv.supplier_order
            optical_wo.create_purchase(order.store.fetch(rv.supplier),
                                       order.store.fetch(rv.item),
                                       rv.is_freebie, api.get_current_branch(order.store),
                                       api.get_current_station(order.store),
                                       api.get_current_user(order.store))
            return

        for purchase in PurchaseOrder.find_by_work_order(order.store, order):
            if optical_wo.can_receive_purchase(purchase):
                optical_wo.receive_purchase(purchase, api.get_current_station(order.store),
                                            api.get_current_user(order.store), reserve=True)

    #
    # Callbacks
    #

    def _on_PrintReportEvent(self, report_class, *args, **kwargs):
        if issubclass(report_class, SaleOrderReport):
            sale = args[0]
            store = sale.store
            workorders = list(WorkOrder.find_by_sale(store, sale))
            if len(workorders):
                print_report(OpticalWorkOrderReceiptReport, workorders)
                return True

        return False

    def _on_patient_history_clicked(self, widget, editor, client):
        run_dialog(OpticalPatientDetails, editor, client.store, client)

    def _on_OpticalPreSale__activate(self, action, parameter):
        self._create_pre_sale()

    def _on_MedicsSearch__activate(self, action, parameter):
        with api.new_store() as store:
            run_dialog(OpticalMedicSearch, None, store, hide_footer=True)

    def _on_MedicSaleItems__activate(self, action, parameter):
        store = api.new_store()
        run_dialog(MedicSalesSearch, None, store, hide_footer=True)
        store.rollback()
