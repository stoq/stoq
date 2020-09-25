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
import urllib.request
import urllib.parse
import urllib.error

from gi.repository import Gtk, GdkPixbuf, Pango, GLib
from kiwi.currency import currency
from kiwi.ui.gadgets import render_pixbuf
from kiwi.ui.objectlist import Column
from storm.expr import And, Or, Eq
from zope.interface import implementer

from stoqlib.api import api
from stoqlib.domain.workorder import (WorkOrder, WorkOrderCategory,
                                      WorkOrderView)
from stoqlib.enums import SearchFilterPosition
from stoqlib.exceptions import InvalidStatus, NeedReason
from stoq.lib.gui.actions.workorder import WorkOrderActions
from stoq.lib.gui.base.dialogs import run_dialog
from stoq.lib.gui.dialogs.workordercategorydialog import WorkOrderCategoryDialog
from stoq.lib.gui.editors.noteeditor import NoteEditor, Note
from stoq.lib.gui.interfaces import ISearchResultView
from stoq.lib.gui.search.personsearch import ClientSearch
from stoq.lib.gui.search.productsearch import ProductSearch
from stoq.lib.gui.search.searchcolumns import IdentifierColumn, SearchColumn
from stoq.lib.gui.search.searchfilters import ComboSearchFilter, DateSearchFilter
from stoq.lib.gui.search.searchresultview import SearchResultListView
from stoq.lib.gui.search.servicesearch import ServiceSearch
from stoq.lib.gui.utils.iconutils import get_workorder_state_icon, render_icon
from stoq.lib.gui.utils.keybindings import get_accels
from stoq.lib.gui.widgets.kanbanview import KanbanView, KanbanViewColumn
from stoqlib.lib.message import info
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.workorder import WorkOrdersReport

from stoq.gui.shell.shellapp import ShellApp

_ = stoqlib_gettext


@implementer(ISearchResultView)
class WorkOrderResultKanbanView(KanbanView):
    status_question_map = {
        WorkOrder.STATUS_WORK_IN_PROGRESS: WorkOrderActions.reopen_question,
        WorkOrder.STATUS_CANCELLED: WorkOrderActions.cancel_question,
        WorkOrder.STATUS_WORK_WAITING: WorkOrderActions.waiting_question,
        WorkOrder.STATUS_WORK_FINISHED: WorkOrderActions.uninform_question,
    }

    need_reason = [
        (WorkOrder.STATUS_WORK_FINISHED, WorkOrder.STATUS_WORK_WAITING),
        (WorkOrder.STATUS_WORK_FINISHED, WorkOrder.STATUS_WORK_IN_PROGRESS),
        # from client informed column to status finished column
        (WorkOrder.STATUS_WORK_FINISHED, WorkOrder.STATUS_WORK_FINISHED),
        (WorkOrder.STATUS_WORK_IN_PROGRESS, WorkOrder.STATUS_WORK_WAITING),
    ]

    status_columns = [
        WorkOrder.STATUS_OPENED,
        WorkOrder.STATUS_WORK_WAITING,
        WorkOrder.STATUS_WORK_IN_PROGRESS,
        WorkOrder.STATUS_WORK_FINISHED
    ]

    def _ask_reason(self, work_order, new_status):
        if (work_order.status, new_status) not in self.need_reason:
            return None

        if work_order.status == new_status and not work_order.is_informed():
            # This will prevent the NoteEditor popup when drag and drop in the
            # same column
            return None

        msg_text = self.status_question_map[new_status]
        rv = run_dialog(NoteEditor, None, work_order.store, model=Note(),
                        message_text=msg_text, label_text=_(u"Reason"),
                        mandatory=True)
        if not rv:
            # False means abort the status change
            return False

        return rv.notes

    def _change_status(self, work_order, new_status):
        with api.new_store() as store:
            work_order = store.fetch(work_order)

            reason = self._ask_reason(work_order, new_status)
            if reason is False:
                store.retval = False
                return

            # FIXME Redo this logic, it wont unset if the user go further back on
            # status
            if work_order.status == new_status:
                if work_order.client_informed_date:
                    work_order.unset_client_informed(reason)
                return True

            try:
                work_order.change_status(new_status, reason)
            except InvalidStatus as e:
                info(str(e))
                store.retval = False
            except NeedReason as e:
                info(str(e), _("Make the change on the order's menu so "
                               "you can specify a reason"))
                store.retval = False

        return store.retval

    def _set_client_informed(self, view):
        # Drag and drop on the same Column
        if view.work_order.client_informed_date:
            return

        rv = run_dialog(NoteEditor, None,
                        view.work_order.store,
                        model=Note(),
                        label_text=WorkOrderActions.inform_question,
                        mandatory=True)
        if not rv:
            return

        with api.new_store() as store:
            work_order = store.fetch(view.work_order)
            # Make the work_order go through all the status
            if not work_order.is_finished():
                work_order.change_status(WorkOrder.STATUS_WORK_FINISHED)

            work_order.inform_client(rv.notes)

    # ISearchResultView

    def attach(self, search, columns):
        self.connect('item-dragged', self._on__item_dragged)
        for status in self.status_columns:
            name = WorkOrder.statuses[status]
            column = KanbanViewColumn(title=name, value=status)
            self.add_column(column)

        # Adding a new column which is not one of |work_order| status
        self.add_column(KanbanViewColumn(title=_('Client informed'),
                                         value='client_informed_date'))
        self.enable_editing()

    def enable_lazy_search(self):
        pass

    def search_completed(self, results):
        # We are only interested in the workorders whose status are in one of our
        # columns
        results = results.find(WorkOrder.status.is_in(self.status_columns))
        for work_order_view in results.order_by(WorkOrder.open_date):
            work_order = work_order_view.work_order
            status_name = WorkOrder.statuses.get(work_order.status)
            # Skip cancel/delivered etc
            if status_name is None:
                continue

            # Since this column isnt one of the |work_order| status
            if work_order.client_informed_date:
                status_name = _('Client informed')

            column = self.get_column_by_title(status_name)
            if column is None:
                continue

            if work_order_view.sellable:
                description = '%s - %s' % (
                    work_order_view.sellable,
                    work_order_view.description)
            else:
                description = work_order_view.description

            # FIXME: Figure out a better way of rendering
            work_order_view.markup = '<b>%s</b>\n%s\n%s' % (
                description,
                str(api.escape(work_order_view.client_name)),
                work_order_view.open_date.strftime('%x'))

            column.append_item(work_order_view)

    def get_settings(self):
        return {}

    def render_item(self, column, renderer, work_order_view):
        renderer.props.margin_color = work_order_view.category_color

    #
    # Kiwi Callbacks
    #

    def _on__item_dragged(self, kanban, column, work_order_view):
        new_status = column.value
        if new_status == 'client_informed_date':
            self._set_client_informed(work_order_view)
            return True

        # Moving through the |work_order|.status will remove the
        # client_informed_date information
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
        self.actions = WorkOrderActions.get_instance()
        super(ServicesApp, self).__init__(*args, **kwargs)

    #
    # Application
    #

    def create_actions(self):
        group = get_accels('app.services')
        actions = [
            # Search
            ("Products", None, _(u"Products..."),
             group.get("search_products")),
            ("Services", None, _(u"Services..."),
             group.get("search_services")),
            ("Categories", None, _(u"Categories..."),
             group.get("search_categories")),
            ("Clients", None, _(u"Clients..."),
             group.get("search_clients")),
        ]
        self.services_ui = self.add_ui_actions(actions)
        radio_actions = [
            ('ViewKanban', '', _("View as Kanban"),
             '', _("Show in Kanban mode")),
            ('ViewList', '', _("View as List"),
             '', _("Show in list mode")),
        ]
        self.add_ui_actions(radio_actions, 'RadioActions')
        self.set_help_section(_(u"Services help"), 'app-services')

    def get_domain_options(self):
        options = [
            ('fa-info-circle-symbolic', _('Details'), 'work_order.Details', True),
            ('fa-edit-symbolic', _('Edit'), 'work_order.Edit', True),
            ('fa-check-symbolic', _('Finish'), 'work_order.FinishOrClose', True),
            ('fa-ban-symbolic', _('Cancel'), 'work_order.Cancel', True),

            ('', _('Deliver'), 'work_order.Close', False),
            # Separator
            ('', _('Approve'), 'work_order.Approve', False),
            ('', _('Pause the work'), 'work_order.Pause', False),
            ('', _('Start the work'), 'work_order.Work', False),
            ('', _('Reject order'), 'work_order.Reject', False),
            ('', _('Check order'), 'work_order.CheckOrder', False),
            ('', _('Inform client'), 'work_order.InformClient', False),
            ('', _('Undo order rejection'), 'work_order.UndoRejection', False),
            ('', _('Repoen order'), 'work_order.Reopen', False),
            # Separator
            ('', _('Print quote'), 'work_order.PrintQuote', False),
            ('', _('Print receipt'), 'work_order.PrintReceipt', False),
        ]
        return options

    def create_ui(self):
        if api.sysparam.get_bool('SMART_LIST_LOADING'):
            self.search.enable_lazy_search()

        self.window.add_print_items2([
            (_("Print quote..."), 'work_order.PrintQuote'),
            (_("Print receipt..."), 'work_order.PrintReceipt'),
        ])
        self.window.add_export_items()
        self.window.add_extra_items2([
            (_("Send orders..."), 'work_order.SendOrders'),
            (_("Receive orders..."), 'work_order.ReceiveOrders'),
        ])
        self.window.add_extra_items([self.ViewKanban, self.ViewList])
        self.window.add_new_items2([
            (_("Work order..."), 'work_order.NewOrder'),
        ])

        self.window.add_search_items([
            self.Products,
            self.Services,
            self.Categories,
            self.Clients,
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

        is_kanban = self.window._current_app_settings.get('show-kanban', False)
        if is_kanban:
            self.ViewKanban.set_state(GLib.Variant.new_boolean(True))
            self.search.set_result_view(WorkOrderResultKanbanView, refresh=refresh)

        if refresh:
            self._update_view()

        self.search.focus_search_entry()

    def deactivate(self):
        # Reset actions to clean up connections
        self.actions = None

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
                    urllib.parse.quote(value),
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
                   column='equipment', data_type=GdkPixbuf.Pixbuf,
                   format_func=render_pixbuf),
            Column('flag_icon', title=_(u'Equipment (Description)'),
                   column='equipment', data_type=GdkPixbuf.Pixbuf,
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
            return render_icon(stock_id, 16)

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
        wo = selection and selection.work_order
        self.actions.set_model(wo)

        finish_btn = self.window.domain_header.get_children()[2]
        finish_btn.set_tooltip_text(_(u"Finish"))
        # If the selected work order is already finished, we change the finish
        # button's label.
        if wo and wo.status == WorkOrder.STATUS_WORK_FINISHED:
            finish_btn.set_tooltip_text(_(u"Deliver"))

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

    def _run_order_category_dialog(self):
        with api.new_store() as store:
            self.run_dialog(WorkOrderCategoryDialog, store)
        self._update_view()
        self._update_filters()

    #
    # Kiwi Callbacks
    #

    def _on_main_filter__row_separator_func(self, model, titer):
        obj = model[titer][1]
        if obj and obj.value == 'sep':
            return True
        return False

    def _on_results__cell_data_func(self, column, renderer, wov, text):
        if not isinstance(renderer, Gtk.CellRendererText):
            return text

        work_order = wov.work_order
        is_finished = work_order.status == WorkOrder.STATUS_WORK_FINISHED
        is_delivered = work_order.status in [WorkOrder.STATUS_CANCELLED,
                                             WorkOrder.STATUS_DELIVERED]
        is_late = work_order.is_late()

        for prop, is_set, value in [
                ('strikethrough', is_delivered, True),
                ('style', is_finished, Pango.Style.ITALIC),
                ('weight', is_late, Pango.Weight.BOLD)]:
            renderer.set_property(prop + '-set', is_set)
            if is_set:
                renderer.set_property(prop, value)

        return text

    def on_search__result_item_popup_menu(self, search, objectlist, item, event):
        self._popover.set_relative_to(objectlist)
        self.show_popover(event)

    def on_search__result_item_activated(self, search, item):
        self.actions.edit_or_details(item.work_order)

    def on_search__result_selection_changed(self, search):
        self._update_list_aware_view()

    def on_results__activate_link(self, results, uri):
        if not uri.startswith('new_order'):
            return

        if '?' in uri:
            category_name = str(urllib.parse.unquote(uri.split('?', 1)[1]))
            category = self.store.find(WorkOrderCategory,
                                       name=category_name).one()
        else:
            category = None

        self.actions.new_order(category=category)

    def on_actions__model_created(self, actions, order):
        self._update_view(select_item=order)
        # A category may have been created on the editor
        self._update_filters()

    def on_actions__model_edited(self, actions, order):
        self._update_view()
        # A category may have been created on the editor
        self._update_filters()

    def on_Products__activate(self, action):
        self.run_dialog(ProductSearch, self.store,
                        hide_footer=True, hide_toolbar=True)

    def on_Services__activate(self, action):
        self.run_dialog(ServiceSearch, self.store)

    def on_Categories__activate(self, action):
        self._run_order_category_dialog()

    def on_Clients__activate(self, button):
        self.run_dialog(ClientSearch, self.store, hide_footer=True)

    def on_ViewList__change_state(self, action, value):
        action.set_state(value)
        if not value.get_boolean():
            return
        self.ViewKanban.set_state(GLib.Variant.new_boolean(not value.get_boolean()))
        self.search.set_result_view(SearchResultListView, refresh=True)
        self._update_list_aware_view()

    def on_ViewKanban__change_state(self, action, value):
        action.set_state(value)
        self.ViewList.set_state(GLib.Variant.new_boolean(not value.get_boolean()))
        self.window._current_app_settings['show-kanban'] = value.get_boolean()
        if not value.get_boolean():
            return
        self.search.set_result_view(WorkOrderResultKanbanView, refresh=True)
        self._update_list_aware_view()
