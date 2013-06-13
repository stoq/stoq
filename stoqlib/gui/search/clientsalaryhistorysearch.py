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

from kiwi.currency import currency

from stoqlib.domain.person import ClientSalaryHistoryView
from stoqlib.gui.search.searchcolumns import SearchColumn
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ClientSalaryHistorySearch(SearchDialog):
    """This search can be used directly, to show all the salaries that have
    been registered to a client
    """

    title = _("Salary History Search")
    search_spec = ClientSalaryHistoryView
    size = (600, 450)

    def __init__(self, store, client=None):
        """
        :param client: the client which salaries will be searched
        """
        self.client = client
        SearchDialog.__init__(self, store)

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['user'])
        self.search.set_query(self.executer_query)

    def get_columns(self):
        columns = [SearchColumn('date', title=_('Date'),
                                data_type=datetime.date, width=150, sorted=True),
                   SearchColumn('new_salary', title=_('Salary'),
                                data_type=currency, width=150),
                   SearchColumn('user', title=_('User'),
                                data_type=str, width=100, expand=True)]

        return columns

    def executer_query(self, store):
        return self.search_spec.find_by_client(self.store, self.client)
