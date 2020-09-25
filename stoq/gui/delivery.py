# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2017 Async Open Source <http://www.async.com.br>
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

"""Delivery app definition."""

import datetime

from gi.repository import Gtk, GdkPixbuf, Pango
from kiwi.ui.objectlist import Column

from stoqlib.api import api
from stoqlib.domain.fiscal import Invoice
from stoqlib.domain.sale import Delivery
from stoqlib.domain.views import DeliveryView
from stoqlib.enums import SearchFilterPosition
from stoq.lib.gui.editors.deliveryeditor import DeliveryEditor
from stoq.lib.gui.search.personsearch import ClientSearch, TransporterSearch
from stoq.lib.gui.search.productsearch import ProductSearch
from stoq.lib.gui.search.searchcolumns import IdentifierColumn, SearchColumn
from stoq.lib.gui.search.searchfilters import ComboSearchFilter
from stoq.lib.gui.search.servicesearch import ServiceSearch
from stoq.lib.gui.utils.iconutils import get_delivery_state_icon, render_icon
from stoqlib.lib.message import yesno
from stoqlib.lib.translation import stoqlib_gettext
from stoq.gui.shell.shellapp import ShellApp

_ = stoqlib_gettext


class DeliveryApp(ShellApp):
    """Delivery app"""

    app_title = _(u'Deliveries')
    gladefile = 'delivery'
    search_spec = DeliveryView
    search_label = _(u'matching:')
    # TODO: Create a report for the view here
    #report_table = DeliveriesReport

    #
    # Application
    #

    def create_actions(self):
        #group = get_accels('app.delivery')
        actions = [
            # Search
            ("Transporters", None, _("Transporters..."),
             # group.get("search_transporters")),
             None),
            ("Clients", None, _("Clients..."),
             # group.get("search_clients")),
             None),
            ("Products", None, _("Products..."),
             # group.get("search_products")),
             None),
            ("Services", None, _("Services..."),
             # group.get("search_services")),
             None),

            # Delivery
            ("Edit", Gtk.STOCK_EDIT, _("Edit..."),
             # group.get('delivery_pick'),
             None,
             _("Edit the selected delivery")),
            ("Pick", None, _("Pick..."),
             # group.get('delivery_pick'),
             None,
             _("Pick the selected delivery")),
            ("Pack", None, _("Pack..."),
             # group.get('delivery_pack'),
             None,
             _("Pack the selected delivery")),
            ("Send", None, _("Send..."),
             # group.get('delivery_send'),
             None,
             _("Send the selected delivery to deliver")),
            ("Receive", Gtk.STOCK_APPLY, _("Mark as received..."),
             # group.get('delivery_receive'),
             None,
             _("Mark the selected delivery as received by the recipient")),
            ("Cancel", Gtk.STOCK_CANCEL, _("Cancel..."),
             # group.get('delivery_cancel'),
             None,
             _("Cancel the selected delivery")),
        ]
        self.delivery_ui = self.add_ui_actions(actions)
        self.set_help_section(_(u"Delivery help"), 'app-delivery')

    def get_domain_options(self):
        options = [
            ('fa-edit-symbolic', _('Edit'), 'delivery.Edit', True),
            ('', _('Pick'), 'delivery.Cancel', False),
            ('', _('Pack'), 'delivery.Cancel', False),
            ('fa-share-square-symbolic', _('Send'), 'delivery.Send', True),
            ('fa-check-square-symbolic', _('Mark as received'), 'delivery.Receive', True),
            ('fa-ban-symbolic', _('Cancel'), 'delivery.Cancel', True),
        ]

        return options

    def create_ui(self):
        self.search.enable_lazy_search()

        # XXX: What should we put on new items?
        self.window.add_new_items([
        ])

        self.window.add_search_items([
            self.Products,
            self.Services,
            self.Transporters,
            self.Clients,
        ])

        # FIXME: identifier is here because it needs an integer column.
        # The lazy summary will actually be taken from the view's
        # post_search_callback
        self.search.set_summary_label(
            column='identifier',
            label=('<b>%s</b>' %
                   api.escape(_('Number of deliveries:'))),
            format='<b>%s</b>',
            parent=self.get_statusbar_message_area())

        self.results.set_cell_data_func(self._on_results__cell_data_func)

    def activate(self, refresh=True):
        self.check_open_inventory()
        if refresh:
            self._update_view()

        self.search.focus_search_entry()

    def search_completed(self, results, states):
        if len(results):
            return

        state = states[1]
        if state is None:
            return

        if state.value is None:
            # Base search with no filters
            base_msg = _("No deliveries could be found.")
            url_msg = ''
        elif state:
            base_msg = {
                Delivery.STATUS_INITIAL: _("No pending deliveries could be found"),
                Delivery.STATUS_CANCELLED: _("No cancelled deliveries could be found"),
                Delivery.STATUS_PICKED: _("No picked deliveries could be found"),
                Delivery.STATUS_PACKED: _("No packed deliveries could be found"),
                Delivery.STATUS_SENT: _("No sent deliveries could be found"),
                Delivery.STATUS_RECEIVED: _("No received deliveries could be found"),
            }[state.value]
            url_msg = ''

        msg = '\n\n'.join([base_msg, url_msg])
        self.search.set_message(msg)

    def create_filters(self):
        self.set_text_field_columns(['recipient_name', 'identifier_str'])

        self.main_filter = ComboSearchFilter(_('Show'), [])
        self.add_filter(self.main_filter, SearchFilterPosition.TOP,
                        callback=self._get_main_query)

        self.create_branch_filter(column=[Invoice.branch_id])
        self._update_filters()

    def get_columns(self):
        return [
            IdentifierColumn('identifier', title=_("Operation #"), sorted=True,
                             width=110, format_func=self._format_identifier),
            SearchColumn('operation_nature', title=_('Operation Nature'),
                         data_type=str),
            SearchColumn('status_str', title=_(u'Status'),
                         search_attribute='status', data_type=str,
                         valid_values=self._get_status_values()),
            SearchColumn('recipient_name', title=_(u'Recipient'),
                         data_type=str, expand=True),
            Column('flag_icon', title=_(u'Status (Description)'),
                   column='recipient_name', data_type=GdkPixbuf.Pixbuf,
                   format_func=self._format_state_icon, format_func_data=True),
            SearchColumn('branch_name', title=_(u'Branch'),
                         data_type=str, visible=False),
            SearchColumn('transporter_name', title=_(u'Transporter'),
                         data_type=str),
            SearchColumn('open_date', title=_(u'Open date'),
                         data_type=datetime.date),
            SearchColumn('cancel_date', title=_(u'Cancel date'),
                         data_type=datetime.date, visible=False),
            SearchColumn('pick_date', title=_(u'Pick date'),
                         data_type=datetime.date, visible=False),
            SearchColumn('pack_date', title=_(u'Pack date'),
                         data_type=datetime.date, visible=False),
            SearchColumn('send_date', title=_(u'Send date'),
                         data_type=datetime.date),
            SearchColumn('receive_date', title=_(u'Receive date'),
                         data_type=datetime.date, visible=False),
        ]

    def set_open_inventory(self):
        pass

    #
    # Private
    #

    def _format_identifier(self, value):
        return str(value).zfill(5)

    def _edit(self):
        delivery = self.search.get_selected_item().delivery
        with api.new_store() as store:
            self.run_dialog(DeliveryEditor, store,
                            model=store.fetch(delivery))

        if store.committed:
            self._update_view()

    def _cancel(self):
        if not yesno(_("This will cancel the delivery. Are you sure?"),
                     Gtk.ResponseType.NO, _(u"Cancel"), _(u"Don't cancel")):
            return

        selection = self.search.get_selected_item()
        with api.new_store() as store:
            delivery = store.fetch(selection.delivery)
            delivery.close()

        self._update_view(select_item=selection)

    def _pick(self):
        if not yesno(_("This will mark the delivery as picked. Are you sure?"),
                     Gtk.ResponseType.NO, _(u"Mark as picked"), _(u"Don't mark")):
            return

        selection = self.search.get_selected_item()
        with api.new_store() as store:
            delivery = store.fetch(selection.delivery)
            delivery.pick(api.get_current_user(store))

        self._update_view(select_item=selection)

    def _pack(self):
        if not yesno(_("This will mark the delivery as packed. Are you sure?"),
                     Gtk.ResponseType.NO, _(u"Mark as packed"), _(u"Don't mark")):
            return

        selection = self.search.get_selected_item()
        with api.new_store() as store:
            delivery = store.fetch(selection.delivery)
            delivery.pack(api.get_current_user(store))

        self._update_view(select_item=selection)

    def _send(self):
        if not yesno(_("This will mark the delivery as sent to the recipient. "
                       "Are you sure?"),
                     Gtk.ResponseType.NO, _(u"Mark as sent"), _(u"Don't mark")):
            return

        selection = self.search.get_selected_item()
        with api.new_store() as store:
            delivery = store.fetch(selection.delivery)
            delivery.send(api.get_current_user(store))

        self._update_view(select_item=selection)

    def _receive(self):
        if not yesno(_("This will mark the delivery as received by the recipient. "
                       "Are you sure?"),
                     Gtk.ResponseType.NO, _(u"Mark as received"), _(u"Don't mark")):
            return

        selection = self.search.get_selected_item()
        with api.new_store() as store:
            delivery = store.fetch(selection.delivery)
            delivery.receive()

        self._update_view(select_item=selection)

    def _format_state_icon(self, item, data):
        # This happens with lazy object lists. Sometimes it calls this function
        # without actually having the real object.
        if not isinstance(item, DeliveryView):
            return

        stock_id, tooltip = get_delivery_state_icon(item.delivery)
        if stock_id is not None:
            return render_icon(stock_id, Gtk.IconSize.MENU)

    def _get_main_query(self, state):
        if state.value is None:
            return True

        return Delivery.status == state.value

    def _get_status_values(self):
        return ([(_('Any'), None)] +
                [(v, k) for k, v in Delivery.statuses.items()])

    def _update_view(self, select_item=None):
        self.refresh()
        if select_item is not None:
            item = self.store.find(DeliveryView, id=select_item.id).one()
            self.select_result(item)
        self._update_list_aware_view()

    def _update_list_aware_view(self):
        selection = self.search.get_selected_item()
        has_selected = bool(selection)
        delivery = has_selected and selection.delivery

        self.set_sensitive([self.Edit], has_selected)
        self.set_sensitive([self.Pick], has_selected and delivery.can_pick())
        self.set_sensitive([self.Pack], has_selected and delivery.can_pack())
        self.set_sensitive([self.Send], has_selected and delivery.can_send())
        self.set_sensitive([self.Receive], has_selected and delivery.can_receive())
        self.set_sensitive([self.Cancel], has_selected and delivery.can_cancel())

    def _update_filters(self):
        items = [(_("All Deliveries"), None)]
        items.extend((status_str, status)
                     for status, status_str in Delivery.statuses.items())
        self.main_filter.update_values(items)

    #
    #  Callbacks
    #

    def _on_results__cell_data_func(self, column, renderer, item, text):
        if not isinstance(renderer, Gtk.CellRendererText):
            return text

        delivery = item.delivery
        is_finished = delivery.status in [Delivery.STATUS_SENT,
                                          Delivery.STATUS_RECEIVED]
        is_waiting = delivery.status == Delivery.STATUS_INITIAL
        is_picked = delivery.status == Delivery.STATUS_PICKED

        for prop, is_set, value in [
                ('strikethrough', is_finished, True),
                ('style', is_picked, Pango.Style.ITALIC),
                ('weight', is_waiting, Pango.Weight.BOLD)]:
            renderer.set_property(prop + '-set', is_set)
            if is_set:
                renderer.set_property(prop, value)

        return text

    def on_search__result_selection_changed(self, search):
        self._update_list_aware_view()

    def on_search__result_item_activated(self, search, item):
        self._edit()

    def on_Edit__activate(self, action):
        self._edit()

    def on_Cancel__activate(self, action):
        self._cancel()

    def on_Pick__activate(self, action):
        self._pick()

    def on_Pack__activate(self, action):
        self._pack()

    def on_Send__activate(self, action):
        self._send()

    def on_Receive__activate(self, action):
        self._receive()

    def on_Products__activate(self, action):
        self.run_dialog(ProductSearch, self.store,
                        hide_footer=True, hide_toolbar=True)

    def on_Transporters__activate(self, action):
        self.run_dialog(TransporterSearch, self.store)

    def on_Services__activate(self, action):
        self.run_dialog(ServiceSearch, self.store)

    def on_Clients__activate(self, button):
        self.run_dialog(ClientSearch, self.store, hide_footer=True)
