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

"""Person Liaisons editor implementation"""


from kiwi.ui.forms import TextField

from stoqlib.api import api
from stoqlib.domain.person import Liaison
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ContactEditor(BaseEditor):
    model_name = _('Liaison')
    model_type = Liaison

    fields = dict(
        name=TextField(_('Name'), mandatory=True, proxy=True),
        phone_number=TextField(_('Phone Number'), mandatory=True, proxy=True),
        )

    def __init__(self, conn, model, person):
        self.person = person
        BaseEditor.__init__(self, conn, model)
        self.set_description(self.model.name)

    #
    # BaseEditor Hooks
    #

    def create_model(self, conn):
        return Liaison(person=self.person, connection=conn)


if __name__ == '__main__':
    ec = api.prepare_test()
    client = ec.create_client()
    run_dialog(ContactEditor, parent=None, conn=ec.trans, model=None,
               person=client.person)
