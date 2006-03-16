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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##
""" NewOrderEditor implementation """

import gettext

from stoqlib.gui.base.editors import BaseEditor
from stoqlib.gui.base.search import get_max_search_results
from stoqlib.domain.sale import Sale
from stoqlib.domain.till import get_current_till_operation
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import IClient, ISalesPerson
from stoqlib.lib.runtime import get_current_user
from stoqlib.lib.parameters import sysparam
from stoqlib.gui.wizards.person import run_person_role_dialog
from stoqlib.gui.editors.person import ClientEditor


_ = gettext.gettext


class NewOrderEditor(BaseEditor):
    model_type = Sale
    gladefile = 'NewOrderEditor'
    proxy_widgets = ('client',
                     'order_number',
                     'salesperson')

    def _setup_client_entry(self):
        client_table = Person.getAdapterClass(IClient)
        clients = client_table.get_active_clients(self.conn)
        clients = clients[:get_max_search_results()]
        items = [(c.get_adapted().name, c) for c in clients]
        self.client.prefill(items)

    def _setup_widgets(self):
        if not sysparam(self.conn).EDIT_SALES_ORDER_NUMBER:
            self.order_number.set_sensitive(False)
        # Waiting for bug 2319
        self.details_button.set_sensitive(False)
        self._setup_client_entry()
        salespersons = Person.iselect(ISalesPerson, connection=self.conn)
        items = [(s.get_adapted().name, s) for s in salespersons]
        self.salesperson.prefill(items)
        self._update_client_widgets()

    def _update_client_widgets(self):
        client_selected = self.client_check.get_active()
        self.client.set_sensitive(client_selected)

    #
    # BaseEditor hooks
    #

    def get_title(self, *args):
        return _('New Order')

    def create_model(self, conn):
        till = get_current_till_operation(conn)
        user = get_current_user()
        salesperson = ISalesPerson(user.get_adapted(), connection=conn)
        return Sale(connection=conn, till=till, salesperson=salesperson)

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    NewOrderEditor.proxy_widgets)

    #
    # Callbacks
    #

    def on_client_button__clicked(self, *args):
        if run_person_role_dialog(ClientEditor, self, self.conn,
                                  self.model.client):
            self.conn.commit()
            # FIXME waiting for entry completion bug fix in kiwi. This part
            # doesn't work properly when editing a client previously set in
            # POS interface
            self._setup_client_entry()

    def on_client_check__toggled(self, *args):
        self._update_client_widgets()

    def on_anonymous_check__toggled(self, *args):
        self._update_client_widgets()
        self.client.model = None
        self.client.set_text('')
