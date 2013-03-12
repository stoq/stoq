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
#

"""Main gui definition for maintenance application"""

import datetime
import urllib

import gtk
from kiwi.currency import currency
from kiwi.enums import SearchFilterPosition
from kiwi.ui.gadgets import render_pixbuf
from kiwi.ui.objectlist import Column, SearchColumn
from kiwi.ui.search import ComboSearchFilter
import pango
from storm.expr import Or

from stoqlib.api import api
from stoqlib.domain.workorder import (WorkOrder, WorkOrderCategory,
                                      WorkOrderView)
from stoqlib.gui.base.search import IdentifierColumn
from stoqlib.gui.dialogs.workordercategorydialog import WorkOrderCategoryDialog
from stoqlib.gui.editors.workordereditor import WorkOrderEditor
from stoqlib.gui.keybindings import get_accels
from stoqlib.gui.printing import print_report
from stoqlib.gui.search.productsearch import ProductSearch
from stoqlib.gui.search.servicesearch import ServiceSearch
from stoqlib.lib.message import yesno
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.workorder import (WorkOrdersReport,
                                         WorkOrderReceiptReport,
                                         WorkOrderQuoteReport)

from stoq.gui.application import SearchableAppWindow

_ = stoqlib_gettext


class _FilterItem(object):
    def __init__(self, name, value, color=None, obj_id=None):
        self.name = name
        self.value = value
        self.color = color
        self.id = obj_id or name

    def __repr__(self):
        return '<_FilterItem "%s">' % (self.name, )


class MaintenanceApp(SearchableAppWindow):
    """Maintenance app"""

    app_name = _(u'Maintenance')
    gladefile = 'maintenance'
    search_table = WorkOrderView
    search_label = _(u'matching:')
    report_table = WorkOrdersReport
    embedded = True

    _status_mapper = {
        'pending': Or(WorkOrder.status == WorkOrder.STATUS_OPENED,
                      WorkOrder.status == WorkOrder.STATUS_APPROVED),
        'in-progress': WorkOrder.status == WorkOrder.STATUS_WORK_IN_PROGRESS,
        'finished': WorkOrder.status == WorkOrder.STATUS_WORK_FINISHED,
        'closed': Or(WorkOrder.status == WorkOrder.STATUS_CANCELLED,
                     WorkOrder.status == WorkOrder.STATUS_CLOSED),
    }

    #
    # Application
    #

    def create_actions(self):
        group = get_accels('app.maintenance')
        actions = [
            # File
            ("OrderMenu", None, _(u"Order")),
            ("NewOrder", None, _(u"Work order..."),
             group.get("new_order")),

            # Search
            ("Products", None, _(u"Products..."),
             group.get("search_products")),
            ("Services", None, _(u"Services..."),
             group.get("search_services")),
            ("Categories", None, _(u"Categories..."),
             group.get("search_categories")),

            # Order
            ("Edit", gtk.STOCK_EDIT, _(u"Edit..."),
             group.get('order_edit'),
             _(u"Edit the selected order")),
            ("Finish", gtk.STOCK_APPLY, _(u"Finish..."),
             group.get('order_finish'),
             _(u"Finish the selected order")),
            ("Cancel", gtk.STOCK_CANCEL, _(u"Cancel..."),
             group.get('order_cancel'),
             _(u"Cancel the selected order")),
            ("Details", gtk.STOCK_INFO, _(u"Details..."),
             group.get('order_details'),
             _(u"Show details of the selected order")),
            ("PrintQuote", None, _(u"Print quote..."),
             group.get('order_print_quote'),
             _(u"Print a quote report of the selected order")),
            ("PrintReceipt", None, _(u"Print receipt..."),
             group.get('order_print_receipt'),
             _(u"Print a receipt of the selected order")),
        ]

        self.maintenance_ui = self.add_ui_actions("", actions,
                                                  filename="maintenance.xml")

        self.Edit.set_short_label(_(u"Edit"))
        self.Finish.set_short_label(_(u"Finish"))
        self.Edit.props.is_important = True
        self.Finish.props.is_important = True

        self.set_help_section(_(u"Maintenance help"), 'app-maintenance')
        self.popup = self.uimanager.get_widget('/MaintenanceSelection')

    def create_ui(self):
        if api.sysparam(self.store).SMART_LIST_LOADING:
            self.search.search.enable_lazy_search()

        self.app.launcher.add_new_items([
            self.NewOrder,
        ])
        self.app.launcher.add_search_items([
            self.Products,
            self.Services,
            self.Categories,
        ])

        self.search.set_summary_label(
            column='total',
            label=('<b>%s</b>' %
                   api.escape(_('Total:'))),
            format='<b>%s</b>',
            parent=self.get_statusbar_message_area())

        self.results.set_cell_data_func(self._on_results__cell_data_func)

    def activate(self, params):
        self.app.launcher.NewToolItem.set_tooltip(
            _(u"Create a new work order"))
        self.app.launcher.SearchToolItem.set_tooltip(
            _(u"Search for work order categories"))

        self._update_view()

    def deactivate(self):
        self.uimanager.remove_ui(self.maintenance_ui)

    def setup_focus(self):
        self.search.refresh()

    def new_activate(self):
        self._new_order()

    def search_activate(self):
        self.run_dialog(ProductSearch, self.store,
                        hide_footer=True, hide_toolbar=True)

    def search_completed(self, results, states):
        if len(results):
            return

        base_msg = ''
        url_msg = ''
        state = states[1]
        if state and state.value is None:
            # Base search with no filters
            base_msg = _(u"No work orders could be found.")
            url = u"<a href='new_order'>%s</a>" % (
                api.escape(_(u"create a new work order")), )
            url_msg = _(u"Would you like to %s ?") % (url, )
        else:
            kind, value = state.value.value.split(':')
            # Search filtering by status
            if kind == 'status':
                if value == 'pending':
                    base_msg = _(u"No pending work orders could be found.")
                elif value == 'in-progress':
                    base_msg = _(u"No work orders in progress could be found.")
                elif value == 'finished':
                    base_msg = _(u"No finished work orders could be found.")
                elif value == 'closed':
                    base_msg = _(u"No closed or cancelled work "
                                 u"orders could be found.")
            # Search filtering by category
            elif kind == 'category':
                base_msg = _(u"No work orders in the category %s "
                             u"could be found.") % (
                                 '<b>%s</b>' % (value, ), )
                url = u"<a href='new_order?%s'>%s</a>" % (
                    urllib.quote(value.encode('utf-8')),
                    api.escape(_(u"create a new work order")), )
                url_msg = _(u"Would you like to %s ?") % (url, )

        if not base_msg:
            return

        msg = '\n\n'.join([base_msg, url_msg])
        self.search.set_message(msg)

    #
    # SearchableAppWindow
    #

    def create_filters(self):
        self.set_text_field_columns(['equipment', 'client_name'])

        self.main_filter = ComboSearchFilter(_('Show'), [])
        combo = self.main_filter.combo
        combo.color_attribute = 'color'
        combo.set_row_separator_func(self._on_main_filter__row_separator_func)

        self.executer.add_filter_query_callback(
            self.main_filter,
            self._on_main_filter__query_callback)
        self.add_filter(self.main_filter, SearchFilterPosition.TOP)

        self._update_filters()

    def get_columns(self):
        return [
            IdentifierColumn('identifier'),
            SearchColumn('work_order.status_str', title=_(u'Status'),
                         search_attribute='status', data_type=str,
                         valid_values=self._get_status_values(), visible=False),
            SearchColumn('category_name', title=_(u'Category'),
                         data_type=str, visible=False),
            SearchColumn('equipment', title=_(u'Equipment'),
                         data_type=str, expand=True, pack_end=True),
            Column('category_color', title=_(u'Equipment'), column='equipment',
                   data_type=gtk.gdk.Pixbuf, format_func=render_pixbuf),
            SearchColumn('client_name', title=_(u'Client'),
                         data_type=str),
            SearchColumn('open_date', title=_(u'Open date'),
                         data_type=datetime.date),
            SearchColumn('approve_date', title=_(u'Approval date'),
                         data_type=datetime.date, visible=False),
            SearchColumn('finish_date', title=_(u'Finish date'),
                         data_type=datetime.date, visible=False),
            SearchColumn('total', title=_(u'Total'),
                         data_type=currency),
        ]

    #
    # Private
    #

    def _get_main_query(self, state):
        item = state.value
        if item is None:
            return

        kind, value = item.value.split(':')
        if kind == 'category':
            return WorkOrder.category_id == item.id
        if kind == 'status':
            return self._status_mapper[value]
        else:
            raise AssertionError(kind, value)

    def _get_status_values(self):
        return ([(_('Any'), None)] +
                [(v, k) for k, v in WorkOrder.statuses.items()])

    def _update_view(self):
        self.search.refresh()
        self._update_list_aware_view()

    def _update_list_aware_view(self):
        selection = self.results.get_selected()
        has_selected = bool(selection)
        has_quote = has_selected and bool(selection.work_order.defect_detected)

        can_edit = (has_selected and (selection.work_order.can_approve() or
                                      selection.work_order.can_start() or
                                      selection.work_order.can_finish()))
        self.set_sensitive([self.Edit], can_edit)
        self.set_sensitive([self.Details], has_selected)
        self.set_sensitive([self.Finish],
                           has_selected and selection.work_order.can_finish())
        self.set_sensitive([self.Cancel],
                           has_selected and selection.work_order.can_cancel())
        self.set_sensitive([self.PrintReceipt],
                           has_selected and selection.work_order.is_finished())
        self.set_sensitive([self.PrintQuote], has_quote)

    def _update_filters(self):
        options = [
            _FilterItem(_(u'Pending'), 'status:pending'),
            _FilterItem(_(u'In progress'), 'status:in-progress'),
            _FilterItem(_(u'Finished'), 'status:finished'),
            _FilterItem(_(u'Closed or cancelled'), 'status:closed'),
        ]

        categories = list(self.store.find(WorkOrderCategory))
        if len(categories):
            options.append(_FilterItem('sep', 'sep'))
        for category in categories:
            value = 'category:%s' % (category.name, )
            options.append(_FilterItem(category.name, value,
                                       color=category.color,
                                       obj_id=category.id))

        self.main_filter.update_values(
            [(_(u'All work orders'), None)] +
            [(item.name, item) for item in options])

    def _new_order(self, category=None):
        with api.trans() as store:
            self.run_dialog(WorkOrderEditor, store,
                            category=store.fetch(category))

        if store.committed:
            self._update_view()
            # A category may have been created on the editor
            self._update_filters()

    def _edit_order(self):
        selection = self.results.get_selected()
        with api.trans() as store:
            self.run_dialog(WorkOrderEditor, store,
                            model=store.fetch(selection.work_order))

        if store.committed:
            self._update_view()
            # A category may have been created on the editor
            self._update_filters()

    def _finish_order(self):
        if yesno(_(u"This will finish the selected order, marking the "
                   u"work as done. Are you sure?"),
                 gtk.RESPONSE_NO, _(u"Don't finish"), _(u"Finish order")):
            return

        selection = self.results.get_selected()
        with api.trans() as store:
            work_order = store.fetch(selection.work_order)
            work_order.finish()

        self._update_view()

    def _cancel_order(self):
        if yesno(_(u"This will cancel the selected order. Are you sure?"),
                 gtk.RESPONSE_NO, _(u"Don't cancel"), _(u"Cancel order")):
            return

        selection = self.results.get_selected()
        with api.trans() as store:
            work_order = store.fetch(selection.work_order)
            work_order.cancel()
        self._update_view()

    def _run_order_details_dialog(self):
        selection = self.results.get_selected()
        self.run_dialog(WorkOrderEditor, self.store,
                        model=selection.work_order, visual_mode=True)

    def _run_order_category_dialog(self):
        with api.trans() as store:
            self.run_dialog(WorkOrderCategoryDialog, store)
        self._update_view()
        self._update_filters()

    #
    # Kiwi Callbacks
    #

    def _on_main_filter__row_separator_func(self, model, titer):
        if model[titer][0] == 'sep':
            return True
        return False

    def _on_main_filter__query_callback(self, state):
        return self._get_main_query(state)

    def _on_results__cell_data_func(self, column, renderer, wov, text):
        if not isinstance(renderer, gtk.CellRendererText):
            return text

        work_order = wov.work_order
        is_finished = work_order.status == WorkOrder.STATUS_WORK_FINISHED
        is_closed = work_order.status in [WorkOrder.STATUS_CANCELLED,
                                          WorkOrder.STATUS_CLOSED]
        is_late = work_order.is_late()

        for prop, is_set, value in [
                ('strikethrough', is_closed, True),
                ('style', is_finished, pango.STYLE_ITALIC),
                ('weight', is_late, pango.WEIGHT_BOLD)]:
            renderer.set_property(prop + '-set', is_set)
            if is_set:
                renderer.set_property(prop, value)

        return text

    def on_results__right_click(self, results, result, event):
        self.popup.popup(None, None, None, event.button, event.time)

    def on_results__row_activated(self, klist, purchase_order_view):
        if self.Edit.get_sensitive():
            self._edit_order()
        elif self.Details.get_sensitive():
            self._run_order_details_dialog()
        else:
            assert False

    def _on_results__double_click(self, results, order):
        if self.Edit.get_sensitive():
            self._edit_order()
        elif self.Details.get_sensitive():
            self._run_order_details_dialog()
        else:
            assert False

    def on_results__selection_changed(self, results, selected):
        self._update_list_aware_view()

    def on_results__activate_link(self, results, uri):
        if not uri.startswith('new_order'):
            return

        if '?' in uri:
            category_name = unicode(urllib.unquote(uri.split('?', 1)[1]))
            category = self.store.find(WorkOrderCategory,
                                       name=category_name).one()
        else:
            category = None

        self._new_order(category=category)

    def on_NewOrder__activate(self, action):
        self._new_order()

    def on_Edit__activate(self, action):
        self._edit_order()

    def on_Finish__activate(self, action):
        self._finish_order()

    def on_Cancel__activate(self, action):
        self._cancel_order()

    def on_Details__activate(self, action):
        self._run_order_details_dialog()

    def on_PrintQuote__activate(self, action):
        workorderview = self.results.get_selected()
        print_report(WorkOrderQuoteReport, workorderview.work_order)

    def on_PrintReceipt__activate(self, action):
        workorderview = self.results.get_selected()
        print_report(WorkOrderReceiptReport, workorderview.work_order)

    def on_Products__activate(self, action):
        self.run_dialog(ProductSearch, self.store,
                        hide_footer=True, hide_toolbar=True)

    def on_Services__activate(self, action):
        self.run_dialog(ServiceSearch, self.store)

    def on_Categories__activate(self, action):
        self._run_order_category_dialog()
