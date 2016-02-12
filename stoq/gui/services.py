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

"""Main gui definition for services application"""

import datetime
import urllib

import gtk
from kiwi.currency import currency
from kiwi.ui.gadgets import render_pixbuf
from kiwi.ui.objectlist import Column
import pango
from storm.expr import And, Or, Eq
from zope.interface import implementer

from stoqlib.api import api
from stoqlib.domain.workorder import (WorkOrder, WorkOrderCategory,
                                      WorkOrderView)
from stoqlib.enums import SearchFilterPosition
from stoqlib.exceptions import InvalidStatus, NeedReason
from stoqlib.gui.dialogs.workordercategorydialog import WorkOrderCategoryDialog
from stoqlib.gui.editors.noteeditor import NoteEditor, Note
from stoqlib.gui.editors.workordereditor import (WorkOrderEditor,
                                                 WorkOrderPackageSendEditor)
from stoqlib.gui.interfaces import ISearchResultView
from stoqlib.gui.search.personsearch import ClientSearch
from stoqlib.gui.search.productsearch import ProductSearch
from stoqlib.gui.search.searchcolumns import IdentifierColumn, SearchColumn
from stoqlib.gui.search.searchfilters import ComboSearchFilter, DateSearchFilter
from stoqlib.gui.search.searchresultview import SearchResultListView
from stoqlib.gui.search.servicesearch import ServiceSearch
from stoqlib.gui.stockicons import STOQ_CLIENTS
from stoqlib.gui.utils.keybindings import get_accels
from stoqlib.gui.utils.printing import print_report
from stoqlib.gui.utils.workorderutils import get_workorder_state_icon
from stoqlib.gui.widgets.kanbanview import KanbanView, KanbanViewColumn
from stoqlib.gui.wizards.workorderpackagewizard import WorkOrderPackageReceiveWizard
from stoqlib.lib.environment import is_developer_mode
from stoqlib.lib.message import yesno, info
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.workorder import (WorkOrdersReport,
                                         WorkOrderReceiptReport,
                                         WorkOrderQuoteReport)
from stoq.gui.shell.shellapp import ShellApp

_ = stoqlib_gettext


@implementer(ISearchResultView)
class WorkOrderResultKanbanView(KanbanView):

    def _change_status(self, work_order, new_status):
        with api.new_store() as store:
            if work_order.status == new_status:
                return True

            work_order = store.fetch(work_order)
            try:
                work_order.change_status(new_status)
            except InvalidStatus as e:
                info(str(e))
                store.retval = False
            except NeedReason as e:
                info(str(e), _("Make the change on the order's menu so "
                               "you can specify a reason"))
                store.retval = False

        return store.retval

    # ISearchResultView

    def attach(self, search, columns):
        self.connect('item-dragged', self._on__item_dragged)
        statuses = list(WorkOrder.statuses.values())
        statuses.remove(_(u'Cancelled'))
        statuses.remove(_(u'Delivered'))
        for status_name in statuses:
            column = KanbanViewColumn(title=status_name)
            self.add_column(column)
        self.enable_editing()

    def enable_lazy_search(self):
        pass

    def search_completed(self, results):
        for work_order_view in results.order_by(WorkOrder.open_date):
            work_order = work_order_view.work_order
            status_name = WorkOrder.statuses.get(work_order.status)
            # Skip cancel/delivered etc
            if status_name is None:
                continue
            column = self.get_column_by_title(status_name)
            if column is None:
                continue
            # FIXME: Figure out a better way of rendering
            work_order_view.markup = '<b>%s - %s</b>\n%s\n%s' % (
                work_order_view.sellable,
                work_order_view.description,
                unicode(api.escape(work_order_view.client_name)),
                work_order_view.open_date.strftime('%x'))

            column.append_item(work_order_view)

    def get_settings(self):
        return {}

    def render_item(self, column, renderer, work_order_view):
        renderer.props.margin_color = work_order_view.category_color

    # Callbacks

    def _on__item_dragged(self, kanban, column, work_order_view):
        for status, status_name in WorkOrder.statuses.items():
            if status_name == column.title:
                new_status = status
                break
        else:
            raise AssertionError

        return self._change_status(work_order_view.work_order,
                                   new_status)


class _FilterItem(object):
    def __init__(self, name, value, color=None, obj_id=None):
        self.name = name
        self.value = value
        self.color = color
        self.id = obj_id or name

    def __repr__(self):
        return '<_FilterItem "%s">' % (self.name, )


class ServicesApp(ShellApp):
    """Services app"""

    app_title = _(u'Services')
    gladefile = 'services'
    search_spec = WorkOrderView
    search_label = _(u'matching:')
    report_table = WorkOrdersReport

    _status_query_mapper = {
        'pending': Or(WorkOrder.status == WorkOrder.STATUS_OPENED,
                      WorkOrder.status == WorkOrder.STATUS_WORK_WAITING),
        'in-progress': WorkOrder.status == WorkOrder.STATUS_WORK_IN_PROGRESS,
        'finished': WorkOrder.status == WorkOrder.STATUS_WORK_FINISHED,
        'delivered': WorkOrder.status == WorkOrder.STATUS_DELIVERED,
        'cancelled': WorkOrder.status == WorkOrder.STATUS_CANCELLED,
        'all-orders': None,
        'not-delivered': And(WorkOrder.status != WorkOrder.STATUS_CANCELLED,
                             WorkOrder.status != WorkOrder.STATUS_DELIVERED),
    }
    _flags_query_mapper = {
        'approved': And(WorkOrder.status != WorkOrder.STATUS_OPENED,
                        WorkOrder.status != WorkOrder.STATUS_CANCELLED),
        'in-transport': Eq(WorkOrder.current_branch_id, None),
        'rejected': Eq(WorkOrder.is_rejected, True),
    }

    def __init__(self, *args, **kwargs):
        self._other_kinds = {}
        super(ServicesApp, self).__init__(*args, **kwargs)

    #
    # Application
    #

    def create_actions(self):
        group = get_accels('app.services')
        actions = [
            # File
            ("OrderMenu", None, _(u"Order")),
            ("NewOrder", None, _(u"Work order..."),
             group.get("new_order")),
            ("SendOrders", None, _(u"Send orders...")),
            ("ReceiveOrders", None, _(u"Receive orders...")),

            # Search
            ("Products", None, _(u"Products..."),
             group.get("search_products")),
            ("Services", None, _(u"Services..."),
             group.get("search_services")),
            ("Categories", None, _(u"Categories..."),
             group.get("search_categories")),
            ("Clients", STOQ_CLIENTS, _(u"Clients..."),
             group.get("search_clients")),

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
            ("DeliverOrder", None, _(u"Deliver...")),
            ("Details", gtk.STOCK_INFO, _(u"Details..."),
             group.get('order_details'),
             _(u"Show details of the selected order")),
            ("PrintQuote", None, _(u"Print quote..."),
             group.get('order_print_quote'),
             _(u"Print a quote report of the selected order")),
            ("PrintReceipt", None, _(u"Print receipt..."),
             group.get('order_print_receipt'),
             _(u"Print a receipt of the selected order")),
            ("Approve", None, _(u"Approve...")),
            ("Pause", None, _(u"Pause the work...")),
            ("Work", None, _(u"Start the work...")),
            ("Reject", None, _(u"Reject order...")),
            ("UndoRejection", None, _(u"Undo order rejection...")),
            ("Reopen", None, _(u"Reopen order...")),
        ]
        self.services_ui = self.add_ui_actions("", actions,
                                               filename="services.xml")

        radio_actions = [
            ('ViewKanban', '', _("View as Kanban"),
             '', _("Show in Kanban mode")),
            ('ViewList', '', _("View as List"),
             '', _("Show in list mode")),
        ]
        self.add_ui_actions('', radio_actions, 'RadioActions',
                            'radio')

        if is_developer_mode():
            self.ViewList.props.active = True
        else:
            self.ViewList.props.visible = False
            self.ViewKanban.props.visible = False
        self.Edit.set_short_label(_(u"Edit"))
        self.Finish.set_short_label(_(u"Finish"))
        self.Edit.props.is_important = True
        self.Finish.props.is_important = True

        self.set_help_section(_(u"Services help"), 'app-services')
        self.popup = self.uimanager.get_widget('/ServicesSelection')

    def create_ui(self):
        if api.sysparam.get_bool('SMART_LIST_LOADING'):
            self.search.enable_lazy_search()

        self.window.add_new_items([
            self.NewOrder,
        ])
        self.window.add_search_items([
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

    def activate(self, refresh=True):
        self.check_open_inventory()

        self.window.NewToolItem.set_tooltip(
            _(u"Create a new work order"))
        self.window.SearchToolItem.set_tooltip(
            _(u"Search for work order categories"))

        if refresh:
            self._update_view()

        self.search.focus_search_entry()

    def deactivate(self):
        self.uimanager.remove_ui(self.services_ui)

    def new_activate(self):
        self.new_order()

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
                elif value == 'delivered':
                    base_msg = _(u"No delivered or cancelled work "
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

    def create_filters(self):
        self.set_text_field_columns(['sellable', 'description',
                                     'client_name', 'identifier_str',
                                     'sale_identifier_str'])

        self.main_filter = ComboSearchFilter(_('Show'), [])
        combo = self.main_filter.combo
        combo.color_attribute = 'color'
        combo.set_row_separator_func(self._on_main_filter__row_separator_func)

        self.add_filter(self.main_filter, SearchFilterPosition.TOP,
                        callback=self._get_main_query)

        self.create_branch_filter(column=[WorkOrder.branch_id,
                                          WorkOrder.current_branch_id])
        self._update_filters()

    def get_columns(self):
        return [
            IdentifierColumn('identifier', title=_('WO #'), sorted=True),
            IdentifierColumn('sale_identifier', title=_("Sale #"), visible=False),
            SearchColumn('status_str', title=_(u'Status'),
                         search_attribute='status', data_type=str,
                         valid_values=self._get_status_values(), visible=False),
            SearchColumn('category_name', title=_(u'Category'),
                         data_type=str, visible=False, multiple_selection=True,
                         search_attribute='category_id',
                         valid_values=self._get_category_values()),
            Column('equipment', title=_(u'Equipment (Description)'),
                   data_type=str, expand=True, pack_end=True),
            Column('category_color', title=_(u'Equipment (Description)'),
                   column='equipment', data_type=gtk.gdk.Pixbuf,
                   format_func=render_pixbuf),
            Column('flag_icon', title=_(u'Equipment (Description)'),
                   column='equipment', data_type=gtk.gdk.Pixbuf,
                   format_func=self._format_state_icon, format_func_data=True),
            SearchColumn('client_name', title=_(u'Client'),
                         data_type=str),
            SearchColumn('branch_name', title=_(u'Branch'),
                         data_type=str, visible=False),
            SearchColumn('current_branch_name', title=_(u'Current branch'),
                         data_type=str, visible=False),
            SearchColumn('execution_branch_name', title=_(u'Execution branch'),
                         data_type=str, visible=False),
            SearchColumn('supplier_order', title=_("Supplier Order #"),
                         visible=False, data_type=str),
            SearchColumn('open_date', title=_(u'Open date'),
                         data_type=datetime.date),
            SearchColumn('approve_date', title=_(u'Approval date'),
                         data_type=datetime.date, visible=False),
            SearchColumn('estimated_start', title=_(u'Estimated start'),
                         data_type=datetime.date, visible=False),
            SearchColumn('estimated_finish', title=_(u'Estimated finish'),
                         data_type=datetime.date, visible=False),
            SearchColumn('finish_date', title=_(u'Finish date'),
                         data_type=datetime.date, visible=False),
            SearchColumn('total', title=_(u'Total'),
                         data_type=currency),
        ]

    def set_open_inventory(self):
        # This needs to be implemented because we are calling check_open_inventory.
        # We won't do anything here tough, WorkOrderEditor will, but we call
        # check_open_inventory to display the open inventory bar and make
        # it explicit for the user that there's an open inventory
        pass

    def search_for_date(self, date):
        self.main_filter.combo.select(self._not_delivered_filter_item)
        dfilter = DateSearchFilter(_("Estimated finish"))
        dfilter.set_removable()
        dfilter.select(data=DateSearchFilter.Type.USER_DAY)
        self.add_filter(dfilter, columns=["estimated_finish"])
        dfilter.start_date.set_date(date)
        self.refresh()

    def add_filters(self, filter_items, kind, mapper):
        """Add additional filter option.

        :param filter_items: list of tuple (name, value, color)
        :param kind:the kind of filter
        :param mapper: a dictionary containing the query for each option
        """
        for item in filter_items:
            option = _FilterItem(item[0], item[1], color=item[2])
            self.main_filter.combo.append_item(option.name, option)
        self._other_kinds[kind] = mapper

    def new_order(self, category=None, available_categories=None):
        with api.new_store() as store:
            work_order = self.run_dialog(WorkOrderEditor, store,
                                         category=store.fetch(category),
                                         available_categories=available_categories)

        if store.committed:
            self._update_view(select_item=work_order)
            # A category may have been created on the editor
            self._update_filters()

    #
    # Private
    #

    def _format_state_icon(self, item, data):
        # This happens with lazy object lists. Sometimes it calls this function
        # without actually having the real object.
        if not isinstance(item, WorkOrderView):
            return

        stock_id, tooltip = get_workorder_state_icon(item.work_order)
        if stock_id is not None:
            # We are using self.results because render_icon is a gtk.Widget's
            # method. It has nothing to do with results tough.
            return self.results.render_icon(stock_id, gtk.ICON_SIZE_MENU)

    def _get_main_query(self, state):
        item = state.value
        kind, value = item.value.split(':')
        if kind in self._other_kinds:
            return self._other_kinds[kind][value]
        elif kind == 'category':
            return WorkOrder.category_id == item.id
        elif kind == 'status':
            return self._status_query_mapper[value]
        elif kind == 'flag':
            return self._flags_query_mapper[value]
        else:
            raise AssertionError(kind, value)

    def _get_status_values(self):
        return ([(_('Any'), None)] +
                [(v, k) for k, v in WorkOrder.statuses.items()])

    def _get_category_values(self):
        return [
            (category.name, category.id, render_pixbuf(category.color))
            for category in self.store.find(WorkOrderCategory)]

    def _update_view(self, select_item=None):
        self.refresh()
        if select_item is not None:
            item = self.store.find(WorkOrderView, id=select_item.id).one()
            self.select_result(item)
        self._update_list_aware_view()

    def _update_list_aware_view(self):
        selection = self.search.get_selected_item()
        has_selected = bool(selection)
        wo = has_selected and selection.work_order

        if wo and wo.sale is not None:
            has_quote = wo.order_items.count() > 0
        else:
            has_quote = wo and bool(wo.defect_reported or wo.defect_detected)

        self.set_sensitive([self.Edit], has_selected and wo.can_edit())
        self.set_sensitive([self.Details], has_selected)
        self.set_sensitive([self.Finish], has_selected and (wo.can_finish() or
                                                            wo.can_close()))
        self.set_sensitive([self.Cancel], has_selected and wo.can_cancel())
        self.set_sensitive([self.PrintReceipt], has_selected and wo.is_finished())
        self.set_sensitive([self.PrintQuote], has_quote)

        self.Finish.set_short_label(_(u"Finish"))
        # If the selected work order is already finished, we change the finish
        # button's label.
        if has_selected and wo.status == WorkOrder.STATUS_WORK_FINISHED:
            self.Finish.set_short_label(_(u"Deliver"))

        for widget, value in [
                (self.Approve, has_selected and wo.can_approve()),
                (self.Reject, has_selected and wo.can_reject()),
                (self.UndoRejection, has_selected and wo.can_undo_rejection()),
                (self.Pause, has_selected and wo.can_pause()),
                (self.Work, has_selected and wo.can_work()),
                (self.Reopen, has_selected and wo.can_reopen()),
                # DeliverOrder is grouped here since it's a special case
                # Only finished orders without items and without sale can be
                # delivered here, so avoid showing the option if it's not
                #sensitive to avoid confusions
                (self.DeliverOrder, (has_selected and wo.can_close() and
                                     not wo.order_items.count() and not wo.sale))]:
            self.set_sensitive([widget], value)
            # Some of those options are mutually exclusive (except Approve,
            # but it can only be called once) so avoid confusions and
            # hide not available options
            widget.set_visible(value)

    def _update_filters(self):
        self._not_delivered_filter_item = _FilterItem(_(u'Not delivered'),
                                                      'status:not-delivered')
        options = [
            self._not_delivered_filter_item,
            _FilterItem(_(u'Pending'), 'status:pending'),
            _FilterItem(_(u'In progress'), 'status:in-progress'),
            _FilterItem(_(u'Finished'), 'status:finished'),
            _FilterItem(_(u'Delivered'), 'status:delivered'),
            _FilterItem(_(u'Cancelled'), 'status:cancelled'),
            _FilterItem(_(u'All work orders'), 'status:all-orders'),
            _FilterItem('sep', 'sep'),
            _FilterItem(_(u'Approved'), 'flag:approved'),
            _FilterItem(_(u'In transport'), 'flag:in-transport'),
            _FilterItem(_(u'Rejected'), 'flag:rejected'),
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
            [(item.name, item) for item in options])

    def _edit_order(self, work_order=None):
        if work_order is None:
            work_order = self.search.get_selected_item().work_order
        with api.new_store() as store:
            self.run_dialog(WorkOrderEditor, store,
                            model=store.fetch(work_order))

        if store.committed:
            self._update_view()
            # A category may have been created on the editor
            self._update_filters()

    def _finish_or_deliver_order(self):
        work_order = self.search.get_selected_item().work_order
        if work_order.status == WorkOrder.STATUS_WORK_FINISHED:
            self._close_order()
        else:
            self._finish_order()

    def _finish_order(self):
        work_order = self.search.get_selected_item().work_order

        if work_order.is_items_totally_reserved():
            msg = _(u"This will finish the selected order, marking the "
                    u"work as done. Are you sure?")
        else:
            msg = _(u"Some items on this work order are not fully reserved. "
                    u"Do you still want to mark it as finished?")

        if not yesno(msg, gtk.RESPONSE_NO,
                     _(u"Finish order"), _(u"Don't finish")):
            return

        with api.new_store() as store:
            work_order = store.fetch(work_order)
            work_order.finish()

        self._update_view()

    def _cancel_order(self):
        msg_text = _(u"This will cancel the selected order. Any reserved items "
                     u"will return to stock. Are you sure?")
        rv = self._run_notes_editor(msg_text=msg_text, mandatory=True)
        if not rv:
            return

        selection = self.search.get_selected_item()
        with api.new_store() as store:
            work_order = store.fetch(selection.work_order)
            work_order.cancel(reason=rv.notes)
        self._update_view()

    def _close_order(self):
        if not yesno(_(u"This will mark the order as delivered. Are you "
                       "sure?"),
                     gtk.RESPONSE_NO, _(u"Mark as delivered"),
                     _(u"Don't mark")):
            return

        selection = self.search.get_selected_item()
        with api.new_store() as store:
            work_order = store.fetch(selection.work_order)
            work_order.close()

        self._update_view(select_item=selection)

    def _approve_order(self):
        if not yesno(_(u"This will inform the order that the client has "
                       u"approved the work. Are you sure?"),
                     gtk.RESPONSE_NO, _(u"Approve"), _(u"Don't approve")):
            return

        selection = self.search.get_selected_item()
        with api.new_store() as store:
            work_order = store.fetch(selection.work_order)
            work_order.approve()

        self._update_view(select_item=selection)

    def _pause_order(self):
        msg_text = _(u"This will inform the order that we are waiting. "
                     u"Are you sure?")
        rv = self._run_notes_editor(msg_text=msg_text, mandatory=True)
        if not rv:
            return

        selection = self.search.get_selected_item()
        with api.new_store() as store:
            work_order = store.fetch(selection.work_order)
            work_order.pause(reason=rv.notes)

        self._update_view(select_item=selection)

    def _work(self):
        selection = self.search.get_selected_item()
        with api.new_store() as store:
            work_order = store.fetch(selection.work_order)
            work_order.work()

        self._update_view(select_item=selection)

    def _reject(self):
        msg_text = _(u"This will reject the order. Are you sure?")
        rv = self._run_notes_editor(msg_text=msg_text, mandatory=True)
        if not rv:
            return

        selection = self.search.get_selected_item()
        with api.new_store() as store:
            work_order = store.fetch(selection.work_order)
            work_order.reject(reason=rv.notes)

        self._update_view(select_item=selection)

    def _undo_rejection(self):
        msg_text = _(u"This will undo the rejection of the order. "
                     u"Are you sure?")
        rv = self._run_notes_editor(msg_text=msg_text, mandatory=False)
        if not rv:
            return

        selection = self.search.get_selected_item()
        with api.new_store() as store:
            work_order = store.fetch(selection.work_order)
            work_order.undo_rejection(reason=rv.notes)

        self._update_view(select_item=selection)

    def _reopen(self):
        msg_text = _(u"This will reopen the order. Are you sure?")
        rv = self._run_notes_editor(msg_text=msg_text, mandatory=True)
        if not rv:
            return

        selection = self.search.get_selected_item()
        with api.new_store() as store:
            work_order = store.fetch(selection.work_order)
            work_order.reopen(reason=rv.notes)

        self._update_view(select_item=selection)

    def _send_orders(self):
        with api.new_store() as store:
            self.run_dialog(WorkOrderPackageSendEditor, store)

        if store.committed:
            self._update_view()

    def _receive_orders(self):
        with api.new_store() as store:
            self.run_dialog(WorkOrderPackageReceiveWizard, store)

        if store.committed:
            self._update_view()

    def _run_order_details_dialog(self):
        selection = self.search.get_selected_item()
        with api.new_store() as store:
            self.run_dialog(WorkOrderEditor, store,
                            model=store.fetch(selection.work_order),
                            visual_mode=True)

    def _run_order_category_dialog(self):
        with api.new_store() as store:
            self.run_dialog(WorkOrderCategoryDialog, store)
        self._update_view()
        self._update_filters()

    def _run_notes_editor(self, msg_text, mandatory):
        return self.run_dialog(NoteEditor, self.store, model=Note(),
                               message_text=msg_text, label_text=_(u"Reason"),
                               mandatory=mandatory)

    #
    # Kiwi Callbacks
    #

    def _on_main_filter__row_separator_func(self, model, titer):
        obj = model[titer][1]
        if obj and obj.value == 'sep':
            return True
        return False

    def _on_results__cell_data_func(self, column, renderer, wov, text):
        if not isinstance(renderer, gtk.CellRendererText):
            return text

        work_order = wov.work_order
        is_finished = work_order.status == WorkOrder.STATUS_WORK_FINISHED
        is_delivered = work_order.status in [WorkOrder.STATUS_CANCELLED,
                                             WorkOrder.STATUS_DELIVERED]
        is_late = work_order.is_late()

        for prop, is_set, value in [
                ('strikethrough', is_delivered, True),
                ('style', is_finished, pango.STYLE_ITALIC),
                ('weight', is_late, pango.WEIGHT_BOLD)]:
            renderer.set_property(prop + '-set', is_set)
            if is_set:
                renderer.set_property(prop, value)

        return text

    def on_search__result_item_popup_menu(self, search, item, event):
        self.popup.popup(None, None, None, event.button, event.time)

    def on_search__result_item_activated(self, search, item):
        if self.Edit.get_sensitive():
            self._edit_order()
        elif self.Details.get_sensitive():
            self._run_order_details_dialog()
        else:
            assert False

    def on_search__result_selection_changed(self, search):
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

        self.new_order(category=category)

    def on_NewOrder__activate(self, action):
        self.new_order()

    def on_SendOrders__activate(self, action):
        self._send_orders()

    def on_ReceiveOrders__activate(self, action):
        self._receive_orders()

    def on_Edit__activate(self, action):
        self._edit_order()

    def on_Finish__activate(self, action):
        self._finish_or_deliver_order()

    def on_Cancel__activate(self, action):
        self._cancel_order()

    def on_Details__activate(self, action):
        self._run_order_details_dialog()

    def on_Approve__activate(self, action):
        self._approve_order()

    def on_Pause__activate(self, action):
        self._pause_order()

    def on_Work__activate(self, action):
        self._work()

    def on_Reject__activate(self, action):
        self._reject()

    def on_UndoRejection__activate(self, action):
        self._undo_rejection()

    def on_Reopen__activate(self, action):
        self._reopen()

    def on_DeliverOrder__activate(self, action):
        self._close_order()

    def on_PrintQuote__activate(self, action):
        workorderview = self.search.get_selected_item()
        print_report(WorkOrderQuoteReport, workorderview.work_order)

    def on_PrintReceipt__activate(self, action):
        workorderview = self.search.get_selected_item()
        print_report(WorkOrderReceiptReport, workorderview.work_order)

    def on_Products__activate(self, action):
        self.run_dialog(ProductSearch, self.store,
                        hide_footer=True, hide_toolbar=True)

    def on_Services__activate(self, action):
        self.run_dialog(ServiceSearch, self.store)

    def on_Categories__activate(self, action):
        self._run_order_category_dialog()

    def on_Clients__activate(self, button):
        self.run_dialog(ClientSearch, self.store, hide_footer=True)

    def on_ViewList__toggled(self, action):
        if not action.get_active():
            return
        self.search.set_result_view(SearchResultListView, refresh=True)
        self._update_list_aware_view()

    def on_ViewKanban__toggled(self, action):
        if not action.get_active():
            return
        self.search.set_result_view(WorkOrderResultKanbanView, refresh=True)
        self._update_list_aware_view()
