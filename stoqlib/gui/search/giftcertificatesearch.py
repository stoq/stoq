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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Evandro Vale Miquelito  <evandro@async.com.br>
##
##
""" Search dialogs for gift certificates """

import gtk

from kiwi.datatypes import currency
from kiwi.enums import SearchFilterPosition
from kiwi.ui.search import ComboSearchFilter

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.domain.sellable import ASellable
from stoqlib.domain.giftcertificate import (GiftCertificateType,
                                            GiftCertificateView)
from stoqlib.gui.base.search import SearchEditor
from stoqlib.gui.base.columns import Column
from stoqlib.gui.editors.giftcertificateeditor import (
    GiftCertificateTypeEditor, GiftCertificateEditor)

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
        self.set_searchbar_labels(_('matching'))

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns([])
        certificates = [(_('Any'), None),
                        (_('Active'), True),
                        (_('Inactive'), False)]
        status_filter = ComboSearchFilter(
            _('Show gift certificate types with status'), certificates)
        self.add_filter(status_filter, SearchFilterPosition.TOP, ['is_active'])

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


class GiftCertificateSearch(SearchEditor):
    """A search dialog for gift certificates. A gift certificate is a
    product that can be sold in POS application
    """
    size = (750, 500)
    title = _('Gift Certificate Search')
    table = GiftCertificateView
    editor_class = GiftCertificateEditor

    def __init__(self, conn, hide_footer=True, hide_toolbar=False):
        SearchEditor.__init__(self, conn, self.table, self.editor_class,
                              hide_footer=hide_footer,
                              hide_toolbar=hide_toolbar,
                              title=self.title)
        self.hide_edit_button()
        self.set_result_strings(_('gift certificate'),
                                _('gift certificates'))
        self.set_searchbar_labels(_('matching'))

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns([])
        statuses = [(value, constant)
                    for constant, value in ASellable.statuses.items()]
        statuses.insert(0, (_('Any'), None))
        status_filter = ComboSearchFilter(
            _('Show gift certificates with status'), statuses)
        status_filter.select(ASellable.STATUS_AVAILABLE)
        self.add_filter(status_filter, SearchFilterPosition.TOP, ['status'])


    #
    # SearchEditor Hooks
    #

    def update_edited_item(self, *args):
        self.search.refresh()

    def get_columns(self):
        return [Column('id', _('Number'), data_type=int,
                       format='%03d', width=80),
                Column('barcode', title=_('Barcode'), data_type=str,
                       visible=True, width=120),
                Column('description', title=_('Type Name'),
                       data_type=str, width=260, expand=True),
                Column('price', title=_('Price'),
                       data_type=currency, width=120),
                Column('on_sale_price', title=_('On Sale Price'),
                       data_type=currency, width=140)]
