# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

"""Search dialogs for :class:`stoqlib.domain.sale.Delivery` objects"""

import datetime

import gtk
import pango
from kiwi.ui.objectlist import Column

from stoqlib.domain.sale import Delivery
from stoqlib.domain.views import DeliveryView
from stoqlib.enums import SearchFilterPosition
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.editors.deliveryeditor import DeliveryEditor
from stoqlib.gui.search.searchcolumns import IdentifierColumn, SearchColumn
from stoqlib.gui.search.searcheditor import SearchEditor
from stoqlib.gui.search.searchfilters import ComboSearchFilter

_ = stoqlib_gettext


class DeliverySearch(SearchEditor):
    """Delivery search implementation"""

    title = _('Delivery Search')
    search_spec = DeliveryView
    editor_class = DeliveryEditor
    has_new_button = False
    size = (750, 450)

    #
    #  SearchEditor hooks
    #

    def _get_status_values(self):
        items = [(value, key) for key, value in Delivery.statuses.items()]
        items.insert(0, (_('Any'), None))
        return items

    def create_filters(self):
        self.set_text_field_columns(['tracking_code', 'transporter_name',
                                     'client_name', 'identifier_str'])

        # Status
        statuses = [(desc, st) for st, desc in Delivery.statuses.items()]
        statuses.insert(0, (_('Any'), None))
        self.status_filter = ComboSearchFilter(_('With status:'), statuses)
        self.status_filter.select(None)
        self.add_filter(self.status_filter, columns=['status'],
                        position=SearchFilterPosition.TOP)

    def get_editor_model(self, viewable):
        return viewable.delivery

    def get_columns(self):
        return [IdentifierColumn('sale_identifier', title=_('Sale #'),
                                 order=gtk.SORT_DESCENDING),
                SearchColumn('status_str', title=_('Status'), data_type=str,
                             search_attribute='status',
                             valid_values=self._get_status_values()),
                Column('address_str', title=_('Address'), data_type=str,
                       expand=True, ellipsize=pango.ELLIPSIZE_END),
                SearchColumn('tracking_code', title=_('Tracking code'),
                             data_type=str),
                SearchColumn('transporter_name', title=_('Transporter'),
                             data_type=str),
                SearchColumn('client_name', title=_('Client'),
                             data_type=str),
                SearchColumn('open_date', title=_('Open date'),
                             data_type=datetime.date, visible=False),
                SearchColumn('deliver_date', title=_('Sent date'),
                             data_type=datetime.date, visible=False),
                SearchColumn('receive_date', title=_('Received date'),
                             data_type=datetime.date, visible=False),
                ]
