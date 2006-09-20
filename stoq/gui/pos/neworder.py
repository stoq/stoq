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

from stoqlib.database.runtime import get_current_user
from stoqlib.gui.base.editors import BaseEditor
from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.sale import Sale
from stoqlib.domain.till import Till
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import (IClient, ISalesPerson, IIndividual,
                                       ICompany)
from stoqlib.lib.parameters import sysparam
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.gui.editors.personeditor import ClientEditor


_ = gettext.gettext


class NewOrderEditor(BaseEditor):
    model_type = Sale
    size = (670, 210)
    gladefile = 'NewOrderEditor'
    proxy_widgets = ('client',
                     'order_number',
                     'cfop_combo',
                     'salesperson',
                     'individual_role_button')

    def _setup_client_entry(self):
        client_table = Person.getAdapterClass(IClient)
        clients = client_table.get_active_clients(self.conn)
        max_results = sysparam(self.conn).MAX_SEARCH_RESULTS
        clients = clients[:max_results]
        items = [(c.person.name, c) for c in clients]
        self.client.prefill(items)

    def _setup_widgets(self):
        cfop_items = [(item.get_description(), item)
                        for item in CfopData.select(connection=self.conn)]
        self.cfop_combo.prefill(cfop_items)
        self._setup_client_entry()
        self._update_client_widgets()
        self._update_client_role_box()
        for radio_button, data_value in [(self.individual_role_button,
                                          Sale.CLIENT_INDIVIDUAL),
                                         (self.company_role_button,
                                          Sale.CLIENT_COMPANY)]:
            radio_button.set_property("data-type", int)
            radio_button.set_property("data-value", data_value)
        if not sysparam(self.conn).ASK_SALES_CFOP:
            self.cfop_combo.hide()
            self.cfop_label.hide()

    def _update_client_widgets(self):
        client_selected = self.client_check.get_active()
        self.client.set_sensitive(client_selected)
        self.details_button.set_sensitive(self.model.client is not None)

    def _update_client_role_box(self):
        if self.model.client:
            person = self.model.client.person
            if (ICompany(person)
                and IIndividual(person)):
                self.clientrole_box.show()
                return
        self.clientrole_box.hide()

    def _update_client_role(self):
        if not self.model.client:
            self.model.client_role = None
            return
        person = self.model.client.person
        if (ICompany(person)
            and not IIndividual(person)):
            self.model.client_role = Sale.CLIENT_COMPANY
        else:
            self.model.client_role = Sale.CLIENT_INDIVIDUAL

    #
    # BaseEditor hooks
    #

    def get_title(self, *args):
        return _('New Order')

    def create_model(self, conn):
        till = Till.get_current(conn)
        user = get_current_user(conn)
        salesperson = ISalesPerson(user.person)
        cfop = sysparam(conn).DEFAULT_SALES_CFOP
        return Sale(connection=conn, till=till, salesperson=salesperson,
                    cfop=cfop, coupon_id=None)

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    NewOrderEditor.proxy_widgets)

    #
    # Callbacks
    #

    def on_client__content_changed(self, combo):
        self._update_client_role_box()
        self._update_client_role()
        self._update_client_widgets()

    def on_details_button__clicked(self, *args):
        if not self.model.client:
            raise ValueError("You should have a client defined at this point")
        run_dialog(ClientDetailsDialog, self, self.conn, self.model.client)

    def on_client_button__clicked(self, *args):
        self.conn.commit()
        client = run_person_role_dialog(ClientEditor, self, self.conn,
                                        self.model.client)
        if client:
            self._setup_client_entry()
            self.model.client = client
            self.proxy.update('client')

    def on_client_check__toggled(self, *args):
        self._update_client_widgets()
        self._update_client_role_box()

    def on_anonymous_check__toggled(self, *args):
        self._update_client_widgets()
        self.model.client = None
        self.proxy.update('client')
        self._update_client_role_box()
