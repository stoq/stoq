# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import datetime

from kiwi.currency import currency
from kiwi.enums import ListType
from kiwi.ui.objectlist import ColoredColumn, Column

from stoqlib.domain.payment.payment import Payment
from stoqlib.gui.base.lists import ModelListDialog, ModelListSlave
from stoqlib.gui.editors.crediteditor import CreditEditor
from stoqlib.gui.search.searchcolumns import IdentifierColumn
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _CreditInfoListSlave(ModelListSlave):
    model_type = Payment
    editor_class = None
    columns = [IdentifierColumn('identifier', title=_('Payment #'), sorted=True),
               Column('paid_date', title=_(u'Date'), data_type=datetime.date,
                      width=150),
               Column('description', title=_(u'Description'),
                      data_type=str, width=150, expand=True),
               ColoredColumn('paid_value', title=_(u'Value'), color='red',
                             data_type=currency, width=100,
                             use_data_model=True,
                             data_func=lambda p: not p.is_outpayment())]

    def __init__(self, *args, **kwargs):
        ModelListSlave.__init__(self, *args, **kwargs)
        self.set_list_type(ListType.ADDONLY)

    def populate(self):
        return self.parent.person.get_credit_transactions()

    def run_editor(self, store, model):
        store.savepoint('before_run_editor_credit')
        retval = self.run_dialog(CreditEditor, store=store,
                                 client=self.parent.person)
        if not retval:
            store.rollback_to_savepoint('before_run_editor_credit')
        return retval


class CreditInfoListDialog(ModelListDialog):
    list_slave_class = _CreditInfoListSlave
    title = _("Credit Transactions")
    size = (700, 250)

    def __init__(self, store, person, reuse_store=False):
        self.person = person
        self.store = store
        ModelListDialog.__init__(self, store, reuse_store=reuse_store)
