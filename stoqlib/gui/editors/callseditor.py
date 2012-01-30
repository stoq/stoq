# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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

import datetime

from stoqlib.api import api
from stoqlib.domain.interfaces import IUser, IClient
from stoqlib.domain.person import Calls, Person
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class CallsEditor(BaseEditor):
    model_type = Calls
    model_name = _("Calls")
    gladefile = 'CallsEditor'
    help_section = 'client-call'
    proxy_widgets = ('date',
                     'person_combo',
                     'description',
                     'message',
                     'attendant')
    size = (400, 300)

    def __init__(self, conn, model, person, person_iface):
        self.person = person
        self.person_iface = person_iface
        BaseEditor.__init__(self, conn, model)
        # If person is not None, this means we already are in this person
        # details dialog. No need for this option
        if person:
            self.details_button.set_sensitive(False)

        if self.model.person:
            self.set_description(_('Call to %s') % self.model.person.name)
        else:
            self.set_description(_('call'))

    def create_model(self, conn):
        return Calls(date=datetime.date.today(),
                     description='',
                     message='',
                     person=self.person,
                     attendant=api.get_current_user(self.conn),
                     connection=conn)

    def setup_proxies(self):
        self._fill_attendant_combo()
        self._fill_person_combo()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    def _fill_person_combo(self):
        if self.model.person:
            self.person_combo.prefill([(self.model.person.name,
                                        self.model.person)])
            self.person_combo.set_sensitive(False)
        else:
            persons = [(p.person.name, p.person)
                         for p in Person.iselect(self.person_iface,
                                                 connection=self.conn)]
            self.person_combo.prefill(sorted(persons))

    def _fill_attendant_combo(self):
        attendants = [(a.person.name, a)
                     for a in Person.iselect(IUser,
                                             connection=self.conn)]
        self.attendant.prefill(sorted(attendants))

    def on_details_button__clicked(self, button):
        from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
        client = IClient(self.model.person, None)
        if client:
            run_dialog(ClientDetailsDialog, self, self.conn, client)
