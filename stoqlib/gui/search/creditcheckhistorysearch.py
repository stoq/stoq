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

import datetime

import gtk

from kiwi.ui.objectlist import SearchColumn, Column

from stoqlib.api import api
from stoqlib.domain.person import CreditCheckHistoryView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.search import SearchEditor
from stoqlib.gui.editors.creditcheckhistoryeditor import CreditCheckHistoryEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class CreditCheckHistorySearch(SearchEditor):
    """
    """
    title = _("Client Credit Check History Search")
    editor_class = CreditCheckHistoryEditor
    search_table = CreditCheckHistoryView
    size = (700, 450)

    def __init__(self, conn, client=None, reuse_transaction=False):
        """
        :param client: If not None, the search will show only call made to
            this client.
        :param reuse_transaction: When False, a new transaction will be
            created/commited when creating a new call. When True, no transaction
            will be created. In this case, I{conn} will be utilized.
        """
        self.conn = conn
        self.client = client
        self._reuse_transaction = reuse_transaction
        SearchEditor.__init__(self, conn)
        self.set_edit_button_label(_('Details'), gtk.STOCK_INFO)

    #
    # SearchEditor Hooks
    #

    def get_editor_model(self, credit_check_history):
        return credit_check_history.check_history

    def create_filters(self):
        if self.client:
            self.set_text_field_columns(['identifier'])
        else:
            self.set_text_field_columns(['identifier', 'client_name'])
        self.set_searchbar_labels(_('matching:'))
        self.executer.set_query(self.executer_query)

    def get_columns(self):
        columns = [SearchColumn('check_date', title=_('Date'),
                                data_type=datetime.date, width=150, sorted=True),
                   SearchColumn('identifier', title=_('Identifier'),
                                data_type=str, width=130),
                   Column('status', title=_('Status'),
                          data_type=str, width=160),
                   Column('notes', title=_('Notes'),
                          data_type=str, width=100, expand=True),
                   SearchColumn('user', title=_('User'),
                                data_type=str, width=100)]
        if not self.client:
            columns.insert(1, SearchColumn('client_name', title=_('Client'),
                           data_type=str, width=150, expand=True))
        return columns

    def executer_query(self, query, having, conn):
        return self.search_table.select_by_client(query, self.client,
                          connection=self.conn).orderBy(
                                    CreditCheckHistoryView.q.check_date,
                                    CreditCheckHistoryView.q.id)

    def update_widgets(self, *args):
        call_view = self.results.get_selected()
        self.set_edit_button_sensitive(call_view is not None)

    def run_editor(self, obj):
        visual_mode = obj is not None
        if self._reuse_transaction:
            self.conn.savepoint('before_run_editor_client_history')
            retval = run_dialog(self.editor_class, self, self.conn,
                                self.conn.get(obj), self.conn.get(self.client),
                                visual_mode=visual_mode)
            if not retval:
                self.conn.rollback_to_savepoint('before_run_editor_client_history')
        else:
            trans = api.new_transaction()
            client = trans.get(self.client)
            retval = run_dialog(self.editor_class, self, trans,
                                trans.get(obj), trans.get(client), visual_mode=visual_mode)
            api.finish_transaction(trans, retval)
            trans.close()
        return retval
