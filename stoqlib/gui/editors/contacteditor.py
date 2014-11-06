# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source <http://www.async.com.br>
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

"""Person Contacts editor implementation
Allows editing of contact information. The user can add a description to each
contact information and the information itself. Both fields are pure text and
there's no phone number formatting."""

import collections

from kiwi.ui.forms import TextField

from stoqlib.api import api
from stoqlib.domain.person import ContactInfo
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ContactInfoEditor(BaseEditor):
    model_name = _('Contact Info')
    model_type = ContactInfo

    confirm_widgets = ['description', 'contact_info']

    @cached_property()
    def fields(self):
        return collections.OrderedDict(
            description=TextField(_('Description'), mandatory=True, proxy=True),
            contact_info=TextField(_('Contact Info'), mandatory=True, proxy=True),
        )

    def __init__(self, store, model=None, person=None):
        self.person = person
        BaseEditor.__init__(self, store, model)
        self.set_description(self.model.description)

    #
    # BaseEditor Hooks
    #

    def create_model(self, store):
        return ContactInfo(person=self.person, store=store)


if __name__ == '__main__':  # pragma nocover
    ec = api.prepare_test()
    client = ec.create_client()
    run_dialog(ContactInfoEditor, parent=None, store=ec.store, model=None,
               person=client.person)
