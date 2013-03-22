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

from stoqlib.api import api
from stoqlib.domain.person import Calls, LoginUser, Person
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.dateutils import localtoday
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

    def __init__(self, store, model, person, person_type):
        self.person = person
        self.person_type = person_type
        BaseEditor.__init__(self, store, model)
        # If person is not None, this means we already are in this person
        # details dialog. No need for this option
        if person:
            self.details_button.hide()

        self.details_button.set_sensitive(self.model.person is not None)
        if self.model.person:
            self.set_description(_('Call to %s') % self.model.person.name)
        else:
            self.set_description(_('call'))

    def create_model(self, store):
        return Calls(date=localtoday().date(),
                     description=u'',
                     message=u'',
                     person=self.person,
                     attendant=api.get_current_user(self.store),
                     store=store)

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
            # Get only persons of person_type by joining with the table
            query = (self.person_type.person_id == Person.id)
            persons = self.store.find(Person, query)
            self.person_combo.prefill(api.for_combo(persons, attr='name'))

    def _fill_attendant_combo(self):
        login_users = self.store.find(LoginUser)
        self.attendant.prefill(api.for_person_combo(login_users))

    def on_details_button__clicked(self, button):
        from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
        client = self.model.person.client
        if client:
            run_dialog(ClientDetailsDialog, self, self.store, client)

    def on_person_combo__changed(self, combo):
        self.details_button.set_sensitive(combo.read() is not None)
