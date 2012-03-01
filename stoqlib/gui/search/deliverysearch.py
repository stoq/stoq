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
from kiwi.enums import SearchFilterPosition
from kiwi.ui.objectlist import Column, SearchColumn
from kiwi.ui.search import ComboSearchFilter

from stoqlib.domain.sale import Delivery
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.editors.deliveryeditor import DeliveryEditor
from stoqlib.gui.base.search import SearchEditor

_ = stoqlib_gettext


class DeliverySearch(SearchEditor):
    """Delivery search implementation"""

    title = _('Delivery Search')
    table = search_table = Delivery
    editor_class = DeliveryEditor
    searchbar_result_strings = _('Delivery'), _('Deliveries')
    has_new_button = False
    size = (750, 450)

    #
    #  SearchEditor hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['tracking_code'])

        # Status
        statuses = [(desc, st) for st, desc in Delivery.statuses.items()]
        statuses.insert(0, (_('Any'), None))
        status_filter = ComboSearchFilter(_('With status:'), statuses)
        status_filter.select(None)
        self.add_filter(status_filter, columns=['status'],
                        position=SearchFilterPosition.TOP)

    def get_columns(self):
        return [Column('id', title=_('#'), data_type=int,
                       order=gtk.SORT_DESCENDING),
                SearchColumn('status_str', title=_('Status'),
                             data_type=str),
                SearchColumn('address_str', title=_('Address'), data_type=str,
                             expand=True, ellipsize=pango.ELLIPSIZE_END),
                SearchColumn('tracking_code', title=_('Tracking code'),
                             data_type=str),
                SearchColumn('transporter', title=_('Transporter'),
                             data_type=str, format_func=self._format_person),
                SearchColumn('client_str', title=_('Client'),
                             data_type=str),
                SearchColumn('open_date', title=_('Open date'),
                             data_type=datetime.date, visible=False),
                SearchColumn('deliver_date', title=_('Sent date'),
                             data_type=datetime.date, visible=False),
                SearchColumn('receive_date', title=_('Received date'),
                             data_type=datetime.date, visible=False),
                ]

    #
    #  Private
    #

    def _format_person(self, person):
        return person.person.name
