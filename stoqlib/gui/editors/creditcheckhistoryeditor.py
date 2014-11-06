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

import collections

from kiwi.ui.forms import ChoiceField, DateField, TextField, MultiLineField

from stoqlib.api import api
from stoqlib.domain.person import Client, CreditCheckHistory
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.fields import PersonField
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class CreditCheckHistoryEditor(BaseEditor):
    model_type = CreditCheckHistory
    model_name = _("Client Credit Check History")
    size = (400, -1)

    @cached_property()
    def fields(self):
        return collections.OrderedDict(
            client_id=PersonField(_('Client'), proxy=True, person_type=Client,
                                  mandatory=True),
            identifier=TextField(_('Identifier'), proxy=True, mandatory=True),
            status=ChoiceField('Status', values=self.get_status_options(),
                               mandatory=True),
            check_date=DateField(_('Date'), proxy=True),
            user=ChoiceField(_('User')),
            notes=MultiLineField(_('Notes'), proxy=True),
        )

    def __init__(self, store, model, client, visual_mode=None):
        self._client = client

        BaseEditor.__init__(self, store, model, visual_mode)

        if visual_mode or client:
            self.client_id_add_button.hide()
            self.client_id_edit_button.hide()

        if self.model.client:
            self.set_description(_('client credit check history for %s') %
                                 self.model.client.person.name)
            self.client_id.set_sensitive(False)
        else:
            self.set_description(_('client credit check history'))

    def create_model(self, store):
        return CreditCheckHistory(check_date=localtoday().date(),
                                  identifier=u'',
                                  status=CreditCheckHistory.STATUS_NOT_INCLUDED,
                                  client=self._client,
                                  notes=u'',
                                  user=api.get_current_user(self.store),
                                  store=store)

    def setup_proxies(self):
        self._fill_user_field()

    def _fill_user_field(self):
        self.user.prefill([(self.model.user.person.name,
                            self.model.user)])
        self.user.set_sensitive(False)

    @classmethod
    def get_status_options(cls):
        return [(value, key) for key, value in CreditCheckHistory.statuses.items()]
