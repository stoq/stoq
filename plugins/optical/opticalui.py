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

import decimal
import logging

import gtk
from storm.expr import LeftJoin

from stoqlib.api import api
from stoqlib.database.runtime import get_default_store
from stoqlib.database.viewable import Viewable
from stoqlib.domain.product import Product, ProductManufacturer
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.workorder import WorkOrder
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.personeditor import ClientEditor
from stoqlib.gui.editors.producteditor import ProductEditor
from stoqlib.gui.editors.workordereditor import WorkOrderEditor
from stoqlib.gui.events import (StartApplicationEvent, StopApplicationEvent,
                                EditorCreateEvent, RunDialogEvent,
                                PrintReportEvent, SearchDialogSetupSearchEvent,
                                ApplicationSetupSearchEvent)
from stoqlib.gui.search.searchcolumns import SearchColumn
from stoqlib.gui.search.searchextension import SearchExtension
from stoqlib.gui.utils.keybindings import add_bindings, get_accels
from stoqlib.gui.utils.printing import print_report
from stoqlib.gui.wizards.personwizard import PersonRoleWizard
from stoqlib.gui.wizards.workorderquotewizard import WorkOrderQuoteWizard
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.sale import SaleOrderReport
from stoq.gui.services import ServicesApp

from .medicssearch import OpticalMedicSearch, MedicSalesSearch
from .opticaleditor import MedicEditor, OpticalWorkOrderEditor
from .opticalhistory import OpticalPatientDetails
from .opticalreport import OpticalWorkOrderReceiptReport
from .opticalslave import ProductOpticSlave, WorkOrderOpticalSlave
from .opticalwizard import OpticalSaleQuoteWizard, MedicRoleWizard
from .opticaldomain import OpticalProduct


_ = stoqlib_gettext
log = logging.getLogger(__name__)


class ProductSearchExtention(SearchExtension):
    spec_attributes = dict(
        gf_glass_type=OpticalProduct.gf_glass_type,
        gf_size=OpticalProduct.gf_size,
        gf_lens_type=OpticalProduct.gf_lens_type,
        gf_color=OpticalProduct.gf_color,
        gl_photosensitive=OpticalProduct.gl_photosensitive,
        gl_anti_glare=OpticalProduct.gl_anti_glare,
        gl_refraction_index=OpticalProduct.gl_refraction_index,
        gl_classification=OpticalProduct.gl_classification,
        gl_addition=OpticalProduct.gl_addition,
        gl_diameter=OpticalProduct.gl_diameter,
        gl_height=OpticalProduct.gl_height,
        gl_availability=OpticalProduct.gl_availability,
        cl_degree=OpticalProduct.cl_degree,
        cl_classification=OpticalProduct.cl_classification,
        cl_lens_type=OpticalProduct.cl_lens_type,
        cl_discard=OpticalProduct.cl_discard,
        cl_addition=OpticalProduct.cl_addition,
        cl_cylindrical=OpticalProduct.cl_cylindrical,
        cl_axis=OpticalProduct.cl_axis,
        cl_color=OpticalProduct.cl_color,
        cl_curvature=OpticalProduct.cl_curvature,
    )
    spec_joins = [
        LeftJoin(OpticalProduct, OpticalProduct.product_id == Product.id)
    ]

    def get_columns(self):
        info_cols = {
            _('Frame'): [
                ('gf_glass_type', _('Glass Type'), str, False),
                ('gf_size', _('Size'), str, False),
                ('gf_lens_type', _('Lens Type'), str, False),
                ('gf_color', _('Color'), str, False),
            ],
            _('Glass Lenses'): [
                ('gl_photosensitive', _('Photosensitive'), str, False),
                ('gl_anti_glare', _('Anti Glare'), str, False),
                ('gl_refraction_index', _('Refraction Index'), decimal.Decimal,
                 False),
                ('gl_classification', _('Classification'), str, False),
                ('gl_addition', _('Addition'), str, False),
                ('gl_diameter', _('Diameter'), str, False),
                ('gl_height', _('Height'), str, False),
                ('gl_availability', _('Availability'), str, False),
            ],
            _('Contact Lenses'): [
                ('cl_degree', _('Degree'), decimal.Decimal, False),
                ('cl_classification', _('Classification'), str, False),
                ('cl_lens_type', _('Lens Type'), str, False),
                ('cl_discard', _('Discard'), str, False),
                ('cl_addition', _('Addition'), str, False),
                ('cl_cylindrical', _('Cylindrical'), decimal.Decimal, False),
                ('cl_axis', _('Axis'), decimal.Decimal, False),
                ('cl_color', _('Color'), str, False),
                ('cl_curvature', _('Curvature'), str, False),
            ],
        }

        columns = []
        for label, columns_list in info_cols.iteritems():
            for c in columns_list:
                columns.append(
                    SearchColumn(c[0], title='%s - %s' % (label, c[1]),
                                 data_type=c[2], visible=c[3]))
        return columns


class ServicesSearchExtention(SearchExtension):
    spec_attributes = dict(
        manufacturer_name=ProductManufacturer.name
    )
    spec_joins = [
        LeftJoin(Product, Product.id == Sellable.id),
        LeftJoin(ProductManufacturer,
                 Product.manufacturer_id == ProductManufacturer.id)
    ]

    def get_columns(self):
        return [
            SearchColumn('manufacturer_name', title=_('Manufacturer'), data_type=str,
                         visible=False)
        ]


class OpticalUI(object):
    def __init__(self):
        # This will contain a mapping of (appname, uimanager) -> extra_ui
        # We need to store that like this because each windows has it's unique
        # uimanager, and we have an extra_ui for different apps
        self._app_ui = dict()

        self.default_store = get_default_store()
        StartApplicationEvent.connect(self._on_StartApplicationEvent)
        StopApplicationEvent.connect(self._on_StopApplicationEvent)
        EditorCreateEvent.connect(self._on_EditorCreateEvent)
        RunDialogEvent.connect(self._on_RunDialogEvent)
        PrintReportEvent.connect(self._on_PrintReportEvent)
        SearchDialogSetupSearchEvent.connect(self._on_SearchDialogSetupSearchEvent)
        ApplicationSetupSearchEvent.connect(self._on_ApplicationSetupSearchEvent)

        add_bindings([
            ('plugin.optical.pre_sale', ''),
            ('plugin.optical.search_medics', ''),
        ])

    #
    # Private
    #

    def _add_sale_menus(self, sale_app):
        uimanager = sale_app.uimanager
        ui_string = """
        <ui>
            <menubar name="menubar">
                <placeholder name="ExtraMenubarPH">
                    <menu action="OpticalMenu">
                    <menuitem action="OpticalPreSale"/>
                    <menuitem action="OpticalMedicSaleItems"/>
                    <menuitem action="OpticalMedicSearch"/>
                    </menu>
                </placeholder>
            </menubar>
        </ui>
        """

        group = get_accels('plugin.optical')
        ag = gtk.ActionGroup('OpticalSalesActions')
        ag.add_actions([
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
        ])

        uimanager.insert_action_group(ag, 0)
        self._app_ui[('sales', uimanager)] = uimanager.add_ui_from_string(ui_string)

    def _add_services_menus(self, services_app):
        uimanager = services_app.uimanager
        ui_string = """
        <ui>
            <menubar name="menubar">
                <placeholder name="AppMenubarPH">
                    <menu action="OrderMenu">
                        <separator/>
                        <menuitem action="OpticalDetails"/>
                    </menu>
                </placeholder>
            </menubar>
            <popup name="ServicesSelection">
                <placeholder name="ServicesSelectionPH">
                    <separator/>
                    <menuitem action="OpticalDetails"/>
                </placeholder>
            </popup>
        </ui>
        """

        ag = gtk.ActionGroup('OpticalServicesActions')
        ag.add_actions([
            ('OpticalDetails', None, _(u'Edit optical details...'),
             None, None,
             self._on_OpticalDetails__activate),
        ])

        uimanager.insert_action_group(ag, 0)
        self._app_ui[('services', uimanager)] = uimanager.add_ui_from_string(ui_string)

        services_app.search.connect(
            'result-selection-changed',
            self._on_ServicesApp__result_selection_changed, uimanager)

    def _remove_app_ui(self, appname, uimanager):
        ui = self._app_ui.pop((appname, uimanager), None)
        if ui is not None:
            uimanager.remove_ui(ui)

    def _fix_work_order_editor(self, editor, model, store):
        slave = WorkOrderOpticalSlave(store, model, show_finish_date=False,
                                      visual_mode=editor.visual_mode)
        editor.add_extra_tab('Ótico', slave)

        def _print_report(button):
            print_report(OpticalWorkOrderReceiptReport, [model])

        # Also add an print button
        if editor.edit_mode:
            print_button = editor.add_button(_('Print'), gtk.STOCK_PRINT)
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

    def _on_StopApplicationEvent(self, appname, app):
        self._remove_app_ui(appname, app.uimanager)

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

    def _on_OpticalPreSale__activate(self, action):
        self._create_pre_sale()

    def _on_MedicsSearch__activate(self, action):
        with api.new_store() as store:
            run_dialog(OpticalMedicSearch, None, store, hide_footer=True)

    def _on_MedicSaleItems__activate(self, action):
        store = api.new_store()
        run_dialog(MedicSalesSearch, None, store, hide_footer=True)
        store.rollback()

    def _on_OpticalDetails__activate(self, action):
        wo_view = self._current_app.search.get_selected_item()

        with api.new_store() as store:
            work_order = store.fetch(wo_view.work_order)
            run_dialog(OpticalWorkOrderEditor, None, store, work_order)

    def _on_ServicesApp__result_selection_changed(self, search, uimanager):
        optical_details = uimanager.get_action(
            '/menubar/AppMenubarPH/OrderMenu/OpticalDetails')
        optical_details.set_sensitive(bool(search.get_selected_item()))
