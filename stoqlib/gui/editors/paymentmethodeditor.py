# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2008 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##
""" Editors for payment method management.  """


from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.destination import PaymentDestination
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.search.personsearch import CardProviderSearch
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext


class PaymentMethodEditor(BaseEditor):
    model_name = _('Payment Method')
    size = (450, 225)
    gladefile = 'PaymentMethodEditor'
    proxy_widgets = ('destination',
                     'max_installments',
                     'interest',
                     'daily_penalty')

    def __init__(self, conn, model):
        """
        Create a new PaymentMethodEditor object.
        @param conn: an orm Transaction instance
        @param model: an adapter of PaymentMethod which means a subclass of
                      PaymentMethod
        """
        self.model_type = PaymentMethod
        BaseEditor.__init__(self, conn, model)
        self.set_description(model.description)


    def _setup_widgets(self):
        destinations = PaymentDestination.select(connection=self.conn)
        items = [(d.get_description(), d) for d in destinations]
        self.destination.prefill(items)

    #
    # BaseEditor Hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model, PaymentMethodEditor.proxy_widgets)


class CardPaymentMethodEditor(PaymentMethodEditor):

    def __init__(self, conn, model):
        PaymentMethodEditor.__init__(self, conn, model)
        button = self.add_button(_(u'Edit providers'))
        button.connect('clicked', self._on_edit_buton_clicked)

    def _on_edit_buton_clicked(self, button):
        run_dialog(CardProviderSearch, self, self.conn)


class MoneyPaymentMethodEditor(PaymentMethodEditor):

    def __init__(self, conn, model):
        PaymentMethodEditor.__init__(self, conn, model)
        self.slave_holder.hide()
