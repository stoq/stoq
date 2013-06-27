# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2013 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

""" Client credit report implementation """

from stoqlib.reporting.report import HTMLReport
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.translation import stoqlib_gettext as _


class ClientCreditReport(HTMLReport):
    """Create letter of credit report"""
    template_filename = 'client_credit/client_credit.html'
    title = _('Letter of Credit')
    complete_header = True
    client = None

    def __init__(self, filename, client):
        self.client = client
        HTMLReport.__init__(self, filename)

    def get_subtitle(self):
        return _(u'Credit letter for %s') % self.client.get_name()

    def get_generated_date(self):
        return localtoday().date()
