# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s): Henrique Romano <henrique@async.com.br>
##
"""
stoq/gui/editors/delivery.py

    Product delivery editor implementation
"""

import gettext
import gtk

from kiwi.ui.widgets.list import Column
from stoqlib.gui.lists import AdditionListSlave, SimpleListDialog
from stoqlib.gui.editors import BaseEditor, NoteEditor
from stoqlib.gui.columns import ForeignKeyColumn
from stoqlib.gui.dialogs import run_dialog

from stoq.lib.parameters import sysparam
from stoq.lib.validators import format_quantity
from stoq.domain.sellable import AbstractSellable
from stoq.domain.service import ServiceSellableItem
from stoq.domain.sale import Sale
from stoq.domain.interfaces import ISellable, IDelivery
from stoq.gui.editors.product import ProductItemEditor

_ = gettext.gettext

class DeliveryEditor(BaseEditor):
    model_type = ServiceSellableItem
    gladefile = 'DeliveryEditor'
    size = (600, 500)

    widgets = ('delivery_date',
               'price',
               'delivery_address',
               'change_address_button', 
               'additional_info_button',
               'additional_info_label',
               'addition_list_holder')

    def __init__(self, conn, model, sale=None, products=None):
        if not model:
            self.title = _('New Delivery ')
        else:
            self.title = _('Edit Delivery')

        self.products = products
        self.sale = sale

        BaseEditor.__init__(self, conn, model)

        self.additional_info_label.set_size('small')
        self.additional_info_label.set_color('Red')

        self.update_widgets()

    def set_widgets_format(self):
        self.price.set_data_format('%.02f')

    def update_widgets(self):
        if self.model.notes:
            self.additional_info_label.show()
        else:
            self.additional_info_label.hide()

    #
    # AdditionListSlave hooks
    #

    def before_delete_items(self, items):
        delivery = IDelivery(self.model, connection=self.conn)
        delivery.remove_items(items)

    def on_edit_item(self, item):
        pass

    #
    # Kiwi handlers
    #

    def on_change_address_button__clicked(self, button):
        cols = [Column('address_string', title=_('Address'), data_type=str, 
                       expand=True),
                Column('city', title=_('City'), width=100, data_type=str),
                Column('state', title=_('State'), width=50, data_type=str)]

        addresses = self.model.sale.client.get_adapted().addresses
        result = run_dialog(SimpleListDialog, self, cols, 
                            addresses, title=_('Client Addresses'))
        if result:
            text = result.get_address_string()
            self.delivery_address.set_text(text)

    def on_additional_info_button__clicked(self, button):
        if run_dialog(NoteEditor, self, self.conn, self.model, 'notes',
                      title=_('Delivery Instructions')):
            self.update_widgets()

    # 
    # BaseEditor hooks
    #

    def create_model(self, conn):
        if not self.products:
            raise TypeError('This editor (%r) requires a list of '
                            'ProductAdaptToSellableItem objects, since you '
                            'don\'t have a model defined.' % self)
        if not self.sale:
            raise TypeError('This editor (%r) requires a valid Sale object, '
                            'since you don\'t have a model defined.' % self)
        if not self.sale.client.get_adapted().get_main_address():
            raise TypeError('The client "%r" doesn\'t have a main address'
                            % self.sale.client)

        sale = Sale.get(self.sale.id, connection=conn)
        service = sysparam(conn).DELIVERY_SERVICE
        sellable = ISellable(service, connection=conn)

        model = sellable.add_sellable_item(sale, 1, 0.00, 0.00)
        delivery = model.addFacet(IDelivery, connection=conn)
        map(delivery.add_item, self.products)

        main_address = sale.client.get_adapted().get_main_address()
        address_string = ("%s - %s/%s" 
                          % (main_address.get_address_string(),
                             main_address.get_city(), 
                             main_address.get_state()))
        delivery.delivery_address = address_string

        return model

    def setup_proxies(self):
        self.set_widgets_format()
        self.add_proxy(model=IDelivery(self.model, connection=self.conn),
                       widgets=('delivery_date', 'delivery_address'))
        self.add_proxy(model=self.model, widgets=('price', ))

    def setup_slaves(self):
        columns = [ForeignKeyColumn(AbstractSellable, 'code', title=_('Code'), 
                                    data_type=str, sorted=True, 
                                    justify=gtk.JUSTIFY_LEFT, 
                                    obj_field='sellable'),
                   ForeignKeyColumn(AbstractSellable, 'description',
                                    title=_('Description'), data_type=str, 
                                    expand=True, obj_field='sellable'),
                   Column('quantity', title=_('Quantity'), data_type=float, 
                          format_func=format_quantity,
                          justify=gtk.JUSTIFY_RIGHT)]

        delivery = IDelivery(self.model, connection=self.conn)
        items = delivery.get_items()
        self.addition_list_slave = AdditionListSlave(self.conn, self, 
                                                     ProductItemEditor,
                                                     columns, items)
        self.addition_list_slave.hide_add_button()

        self.attach_slave('addition_list_holder', 
                          self.addition_list_slave)

