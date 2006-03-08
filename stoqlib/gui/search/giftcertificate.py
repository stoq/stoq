# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Evandro Vale Miquelito  <evandro@async.com.br>
##
##
""" Search dialogs for gift certificates """

import gtk

from kiwi.datatypes import currency

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.search import SearchEditor
from stoqlib.gui.base.columns import Column
from stoqlib.lib.defaults import ALL_ITEMS_INDEX
from stoqlib.domain.interfaces import ISellable
from stoqlib.domain.giftcertificate import (GiftCertificateType,
                                            GiftCertificate)
from stoqlib.gui.editors.giftcertificate import (GiftCertificateTypeEditor,
                                                 GiftCertificateEditor)
from stoqlib.gui.slaves.filter import FilterSlave

_ = stoqlib_gettext


class GiftCertificateTypeSearch(SearchEditor):
    """A search dialog for gift certificate types"""
    title = _('Gift Certificate Type Search')
    size = (750, 500)
    table = GiftCertificateType
    editor_class = GiftCertificateTypeEditor

    def __init__(self, conn, hide_footer=True):
        SearchEditor.__init__(self, conn, self.table, self.editor_class,
                              hide_footer=hide_footer,
                              title=self.title)
        self.search_bar.set_result_strings(_('gift certificate type'),
                                           _('gift certificate types'))
        self.search_bar.set_searchbar_labels(_('matching'))

    #
    # SearchDialog Hooks
    #

    def get_filter_slave(self):
        certificates = [(_('Active'), True), (_('Inactive'), False)]
        certificates.append((_('Any'), ALL_ITEMS_INDEX))
        self.filter_slave = FilterSlave(certificates, selected=ALL_ITEMS_INDEX)
        self.filter_slave.set_filter_label(_('Show gift certificate types '
                                             'with status'))
        return self.filter_slave

    def after_search_bar_created(self):
        self.filter_slave.connect('status-changed',
                                  self.search_bar.search_items)

    def on_cell_edited(self, klist, obj, attr):
        # Waiting for bug 2177. We should only call commit for
        # self.conn here.
        conn = obj.get_connection()
        conn.commit()

    #
    # SearchEditor Hooks
    #

    def get_columns(self):
        return [Column('base_sellable_info.description',
                       _('Description'), data_type=str,
                       expand=True),
                Column('base_sellable_info.price', _('Price'),
                       data_type=currency, width=90),
                Column('base_sellable_info.max_discount',
                       _('Max Discount'), data_type=float,
                       width=130,
                       justify=gtk.JUSTIFY_RIGHT),
                Column('base_sellable_info.commission',
                       _('Commission'), data_type=float,
                       width=110,
                       justify=gtk.JUSTIFY_RIGHT),
                Column('on_sale_info.on_sale_price', _('On Sale Price'),
                       data_type=currency, width=140),
                Column('is_active', _('Active'), data_type=bool,
                       editable=True)]

    def get_extra_query(self):
        status = self.filter_slave.get_selected_status()
        if status != ALL_ITEMS_INDEX:
            return GiftCertificateType.q.is_active == status


class GiftCertificateSearch(SearchEditor):
    """A search dialog for gift certificates. A gift certificate is a
    product that can be sold in POS application
    """
    title = _('Gift Certificate Search')
    size = (800, 600)
    table = GiftCertificate.getAdapterClass(ISellable)
    editor_class = GiftCertificateEditor

    def __init__(self, conn, hide_footer=True):
        SearchEditor.__init__(self, conn, self.table, self.editor_class,
                              hide_footer=hide_footer,
                              title=self.title)
        self.hide_edit_button()
        self.search_bar.set_result_strings(_('gift certificate'),
                                           _('gift certificates'))
        self.search_bar.set_searchbar_labels(_('matching'))

    #
    # SearchDialog Hooks
    #

    def get_filter_slave(self):
        statuses = [(value, constant)
                        for constant, value in self.table.statuses.items()]
        statuses.append((_('Any'), ALL_ITEMS_INDEX))
        self.filter_slave = FilterSlave(statuses, selected=ALL_ITEMS_INDEX)
        self.filter_slave.set_filter_label(_('Show gift certificates with '
                                             'status'))
        return self.filter_slave

    def after_search_bar_created(self):
        self.filter_slave.connect('status-changed',
                                  self.search_bar.search_items)

    #
    # SearchEditor Hooks
    #

    def get_columns(self):
        return [Column('code', _('Number'), data_type=str,
                       width=120),
                Column('base_sellable_info.description',
                       _('Type Name'), data_type=str, width=260),
                Column('base_sellable_info.price', _('Price'),
                       data_type=currency, width=120),
                Column('on_sale_info.on_sale_price', _('On Sale Price'),
                       data_type=currency, width=120),
                Column('status_string', _('Status'), data_type=str)]

    def get_extra_query(self):
        status = self.filter_slave.get_selected_status()
        if status != ALL_ITEMS_INDEX:
            return self.table.q.status == status
