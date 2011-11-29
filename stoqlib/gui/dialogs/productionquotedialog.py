# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
""" Dialog to create quote group from production orders """


import datetime

from kiwi.ui.objectlist import Column

from stoqlib.api import api
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.production import ProductionOrder
from stoqlib.domain.purchase import PurchaseOrder, QuoteGroup, Quotation
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.message import info
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _TemporaryQuoteGroup(object):

    def _create_purchase_order(self, trans):
        return PurchaseOrder(supplier=sysparam(trans).SUGGESTED_SUPPLIER,
                             branch=api.get_current_branch(trans),
                             status=PurchaseOrder.ORDER_QUOTING,
                             expected_receival_date=None,
                             responsible=api.get_current_user(trans),
                             group=PaymentGroup(connection=trans),
                             connection=trans)

    def create_quote_group(self, productions, trans):
        group = QuoteGroup(connection=trans)
        order = self._create_purchase_order(trans)
        to_quote_items = {}
        for production in productions:
            for material in production.get_material_items():
                if material.to_purchase <= 0:
                    continue

                sellable = material.product.sellable
                quantity = material.to_purchase

                if sellable in to_quote_items:
                    to_quote_items[sellable] += quantity
                else:
                    to_quote_items[sellable] = quantity

        for sellable, quantity in to_quote_items.iteritems():
            order.add_item(sellable, quantity)

        Quotation(group=group, purchase=order, connection=trans)
        return group


class _TemporaryProductionModel(object):
    def __init__(self, production):
        self.selected = True
        self.obj = production

    def get_responsible_name(self):
        return self.obj.responsible.person.name


class ProductionQuoteDialog(BaseEditor):
    gladefile = 'ProductionQuoteDialog'
    model_type = _TemporaryQuoteGroup
    title = _('Purchase Production')
    size = (750, 450)

    def __init__(self, conn):
        BaseEditor.__init__(self, conn, model=None)
        self._setup_widgets()
        self._update_widgets()

    def _setup_widgets(self):
        self.main_dialog.ok_button.set_label(_(u"Create _Quote"))
        # productions list
        self.productions.set_columns(self._get_columns())
        for production in ProductionOrder.selectBy(
                                status=ProductionOrder.ORDER_WAITING,
                                connection=self.conn):
            self.productions.append(_TemporaryProductionModel(production))

    def _update_widgets(self):
        all_selected = all([c.selected for c in self.productions])
        self.select_all.set_sensitive(not all_selected)

        has_selected = self._has_selected()
        self.unselect_all.set_sensitive(has_selected)
        self.refresh_ok(has_selected)

    def _get_columns(self):
        return [Column('selected', title=" ", width=50,
                        data_type=bool, editable=True),
                Column('obj.id', title=_(u"Order"), data_type=int,
                        format="%04d"),
                Column('obj.description', title=_(u"Description"),
                        data_type=str, sorted=True),
                Column('obj.responsible_name', title=_(u"Responsible"),
                        data_type=str),
                Column('obj.open_date', title=_(u"Opened"),
                        data_type=datetime.date)]

    def _select(self, productions, select_value):
        for production in productions:
            production.selected = select_value
            self.productions.update(production)
        self._update_widgets()

    def _select_all(self):
        self._select(self.productions, True)

    def _unselect_all(self):
        self._select(self.productions, False)

    def _has_selected(self):
        return any([c.selected for c in self.productions])

    #
    # BaseEditorSlave
    #

    def create_model(self, conn):
        return _TemporaryQuoteGroup()

    def on_confirm(self):
        # We are using this hook as a callback for the OK button
        productions = [p.obj for p in self.productions if p.selected]
        trans = api.new_transaction()
        group = self.model.create_quote_group(productions, trans)
        api.finish_transaction(trans, group)
        trans.close()
        info(_(u'The quote group was succesfully created and it is available '
                'in the Purchase application.'))
        return True

    #
    # Kiwi Callback
    #

    def on_select_all__clicked(self, widget):
        self._select_all()

    def on_unselect_all__clicked(self, widget):
        self._unselect_all()

    def on_productions__cell_edited(self, widget, model, attr):
        self._update_widgets()
